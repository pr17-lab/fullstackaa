import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine
from app.core.config import settings
from sqlalchemy.orm import sessionmaker
from app.models.user import User

engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

user = db.query(User).first()
print(f'Email: {user.email}')
print(f'Has password_hash: {user.password_hash is not None}')
if user.password_hash:
    print(f'Hash length: {len(user.password_hash)}')
    print(f'Hash preview: {user.password_hash[:20]}...')
    print(f'Hash starts with bcrypt marker ($2b$): {user.password_hash.startswith("$2b$")}')

db.close()
