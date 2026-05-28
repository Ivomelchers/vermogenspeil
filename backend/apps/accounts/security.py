import hashlib
import secrets
import string

from apps.accounts.models import EmailVerificationToken, PasswordResetToken


def generate_hashed_secure_token(length=32):
    characters = string.ascii_letters + string.digits
    while True:
        plain_token = "".join(secrets.choice(characters) for _ in range(length))
        hashed_token = hashlib.sha256(plain_token.encode()).hexdigest()
        if not PasswordResetToken.objects.filter(token=hashed_token).exists():
            if not EmailVerificationToken.objects.filter(token=hashed_token).exists():
                return plain_token, hashed_token
