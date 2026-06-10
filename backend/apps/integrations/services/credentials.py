from apps.accounts.utils.encryption import encrypt_value


def store_api_credentials(
    connection,
    *,
    api_key: str,
    api_secret: str,
    api_passphrase: str = "",
) -> None:
    connection.api_key_encrypted = encrypt_value(api_key.strip())
    connection.api_secret_encrypted = encrypt_value(api_secret.strip())
    update_fields = ["api_key_encrypted", "api_secret_encrypted", "updated_at"]
    if api_passphrase:
        connection.api_passphrase_encrypted = encrypt_value(api_passphrase.strip())
        update_fields.append("api_passphrase_encrypted")
    connection.save(update_fields=update_fields)
