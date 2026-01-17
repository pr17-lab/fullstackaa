"""Generate a bcrypt hash for password123."""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("password123")
print(f"Bcrypt hash for 'password123':")
print(hashed)
