import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
    tables = [row[0] for row in result]
    
    for table in tables:
        count = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
        print(f"{table},{count}")
