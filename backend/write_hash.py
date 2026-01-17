#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT password_hash FROM users WHERE email = 'priya.sharma@example.com'"
    ))
    
    for row in result:
        hash_val = row.password_hash
        
        # Write to file
        with open('hash_output.txt', 'w') as f:
            f.write(f"Length: {len(hash_val)}\n")
            f.write(f"Value: {hash_val}\n")
            f.write(f"Repr: {repr(hash_val)}\n")
            
        print(f"Hash written to hash_output.txt, length: {len(hash_val)}")
