"""Geleerde CSV-kolomaliases: persoonlijk direct, gedeeld pas na meerdere bevestigingen."""

from __future__ import annotations

import logging

from django.conf import settings
from django.db import transaction

from apps.integrations.csv.column_mapping_constants import (
    CANONICAL_FIELDS,
    CRITICAL_CANONICALS,
    is_forbidden_description_header,
)
from apps.integrations.csv.headers import normalize_header
from apps.integrations.csv.mapping_sanity import (
    is_safe_to_learn_total,
    is_weak_total_header,
)
from apps.integrations.models import (
    LearnedAliasStatus,
    PlatformImportBatch,
    SharedCsvColumnAlias,
    SharedCsvColumnAliasConfirmation,
    UserCsvColumnAlias,
)

logger = logging.getLogger(__name__)

MAX_ALIASES_PER_IMPORT = 20


def global_alias_min_users() -> int:
    return int(getattr(settings, "LEARNED_ALIAS_GLOBAL_MIN_USERS", 2))


def critical_alias_min_users() -> int:
    return int(getattr(settings, "LEARNED_ALIAS_CRITICAL_MIN_USERS", 3))


def is_safe_learned_mapping(
    canonical: str,
    header: str,
    *,
    original_headers: set[str] | list[str],
) -> bool:
    headers = set(original_headers)
    if canonical not in CANONICAL_FIELDS:
        return False
    if not header or header not in headers:
        return False
    if canonical == "description" and is_forbidden_description_header(header):
        return False
    if canonical == "total" and not is_safe_to_learn_total(header, original_headers=list(headers)):
        return False
    return True


def _safe_mappings_from_batch(
    batch: PlatformImportBatch,
    mapped_columns: dict,
) -> dict[str, str]:
    if not isinstance(mapped_columns, dict):
        return {}

    file_headers = {
        value for value in mapped_columns.values() if isinstance(value, str) and value.strip()
    }
    safe: dict[str, str] = {}
    count = 0
    for canonical, header in mapped_columns.items():
        if count >= MAX_ALIASES_PER_IMPORT:
            break
        if not isinstance(canonical, str) or not isinstance(header, str):
            continue
        if not is_safe_learned_mapping(canonical, header, original_headers=file_headers):
            logger.info(
                "Skipped unsafe learned alias %s → %r for platform %s",
                canonical,
                header,
                batch.platform,
            )
            continue
        safe[canonical] = header
        count += 1
    return safe


def lookup_learned_mappings(
    user,
    platform: str,
    header_map: dict[str, str],
) -> dict[str, dict[str, str]]:
    """Persoonlijke + geverifieerde gedeelde aliases voor headers in dit bestand."""
    normalized_in_file = set(header_map.keys())
    user_mapped: dict[str, str] = {}
    shared_mapped: dict[str, str] = {}

    if user and user.is_authenticated:
        for row in UserCsvColumnAlias.objects.filter(user=user, platform=platform):
            if row.header_normalized not in normalized_in_file:
                continue
            header = header_map.get(row.header_normalized)
            if header:
                user_mapped[row.canonical] = header

    for row in SharedCsvColumnAlias.objects.filter(
        platform=platform,
        status=LearnedAliasStatus.VERIFIED,
    ):
        if row.header_normalized not in normalized_in_file:
            continue
        if row.canonical == "total" and is_weak_total_header(row.header_example or row.header_normalized):
            continue
        header = header_map.get(row.header_normalized)
        if header:
            shared_mapped[row.canonical] = header

    return {"user": user_mapped, "shared": shared_mapped}


@transaction.atomic
def record_learned_aliases_from_import(batch: PlatformImportBatch) -> dict:
    """
    Sla kolommapping op na geslaagde AI-import.
    - User: direct bruikbaar voor die user
    - Shared: pending tot LEARNED_ALIAS_GLOBAL_MIN_USERS distinct users bevestigen
    """
    if not batch.ai_used or batch.transactions_imported <= 0:
        return {"user_aliases": 0, "shared_votes": 0, "shared_verified": 0}

    mapped = batch.column_mapping
    if not mapped:
        return {"user_aliases": 0, "shared_votes": 0, "shared_verified": 0}

    safe = _safe_mappings_from_batch(batch, mapped)
    if not safe.get("date") or not safe.get("total"):
        logger.info("Learned aliases skipped: date/total not in safe mapping for batch %s", batch.pk)
        return {"user_aliases": 0, "shared_votes": 0, "shared_verified": 0}

    user_count = 0
    shared_votes = 0
    shared_verified = 0
    min_users = global_alias_min_users()
    critical_min = critical_alias_min_users()

    for canonical, header in safe.items():
        norm = normalize_header(header)
        can_auto_verify_shared = True
        if canonical in CRITICAL_CANONICALS:
            if is_weak_total_header(header):
                can_auto_verify_shared = False
            required_users = critical_min
        else:
            required_users = min_users

        user_alias, created = UserCsvColumnAlias.objects.update_or_create(
            user=batch.user,
            platform=batch.platform,
            header_normalized=norm,
            defaults={
                "canonical": canonical,
                "header_example": header[:255],
                "source_import_batch": batch,
            },
        )
        if not created:
            if user_alias.canonical != canonical:
                continue
            user_alias.use_count += 1
            user_alias.save(update_fields=["use_count", "updated_at"])
        user_count += 1

        shared = SharedCsvColumnAlias.objects.filter(
            platform=batch.platform,
            header_normalized=norm,
        ).first()

        if shared and shared.status == LearnedAliasStatus.DISABLED:
            continue

        if shared and shared.canonical != canonical:
            shared.conflict_count += 1
            shared.save(update_fields=["conflict_count", "updated_at"])
            logger.warning(
                "Shared alias conflict on %s/%s: existing %s, new %s",
                batch.platform,
                norm,
                shared.canonical,
                canonical,
            )
            continue

        if not shared:
            shared = SharedCsvColumnAlias.objects.create(
                platform=batch.platform,
                canonical=canonical,
                header_normalized=norm,
                header_example=header[:255],
                status=LearnedAliasStatus.PENDING,
                first_import_batch=batch,
            )

        _, vote_created = SharedCsvColumnAliasConfirmation.objects.get_or_create(
            alias=shared,
            user=batch.user,
            defaults={"import_batch": batch},
        )
        if vote_created:
            shared_votes += 1

        distinct_users = (
            SharedCsvColumnAliasConfirmation.objects.filter(alias=shared)
            .values("user")
            .distinct()
            .count()
        )
        shared.confirmation_count = distinct_users
        update_fields = ["confirmation_count", "updated_at"]

        if (
            can_auto_verify_shared
            and shared.status == LearnedAliasStatus.PENDING
            and distinct_users >= required_users
        ):
            shared.status = LearnedAliasStatus.VERIFIED
            update_fields.append("status")
            shared_verified += 1
            logger.info(
                "Shared alias verified: %s/%s → %s (%s users)",
                batch.platform,
                norm,
                canonical,
                distinct_users,
            )

        shared.save(update_fields=update_fields)

    return {
        "user_aliases": user_count,
        "shared_votes": shared_votes,
        "shared_verified": shared_verified,
    }
