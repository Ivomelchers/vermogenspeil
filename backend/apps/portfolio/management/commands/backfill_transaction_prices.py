"""Vul price_eur op kooptransacties aan uit total_eur (na oude DEGIRO-imports)."""

from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.portfolio.models import Portfolio, Transaction, TransactionType
from apps.portfolio.services.position_costs import recompute_position_average_costs
from apps.portfolio.services.transaction_amounts import effective_unit_price_eur


class Command(BaseCommand):
    help = "Zet price_eur op BUY-transacties waar alleen total_eur bekend is; hertel gem. kostprijs."

    def add_arguments(self, parser):
        parser.add_argument("--user-email", type=str, default="", help="Alleen deze gebruiker")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        email = (options["user_email"] or "").strip()

        qs = Transaction.objects.filter(transaction_type=TransactionType.BUY)
        if email:
            qs = qs.filter(portfolio__user__email=email)

        updated_tx = 0
        portfolios_seen: set[int] = set()

        for tx in qs.select_related("portfolio"):
            if tx.price_eur and tx.price_eur > 0:
                continue
            unit = effective_unit_price_eur(
                quantity=tx.quantity,
                price_eur=tx.price_eur,
                total_eur=tx.total_eur,
            )
            if unit is None:
                continue
            portfolios_seen.add(tx.portfolio_id)
            if dry_run:
                self.stdout.write(
                    f"Would set tx {tx.id}: price_eur={unit} (total={tx.total_eur})"
                )
            else:
                tx.price_eur = unit
                tx.save(update_fields=["price_eur", "updated_at"])
            updated_tx += 1

        if not dry_run:
            for portfolio_id in portfolios_seen:
                portfolio = Portfolio.objects.get(pk=portfolio_id)
                recompute_position_average_costs(portfolio)

        self.stdout.write(
            self.style.SUCCESS(
                f"{'Would update' if dry_run else 'Updated'} {updated_tx} transactie(s), "
                f"{len(portfolios_seen)} portefeuille(s)."
            )
        )
