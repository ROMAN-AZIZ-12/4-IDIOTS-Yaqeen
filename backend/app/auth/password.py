"""bcrypt password hashing with the project's configured rounds."""
import bcrypt


def hash_password(plain: str) -> str:
    """Hash a UTF-8 password and return an ascii string for storage."""
    encoded = plain.encode("utf-8")
    if len(encoded) > 72:
        raise ValueError("password exceeds bcrypt byte limit")
    return bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
    except (ValueError, AttributeError):
        return False
