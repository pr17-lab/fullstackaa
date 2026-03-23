#!/usr/bin/env python3
import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env')
DATABASE_URL = os.getenv("DATABASE_URL")

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # 2. Verify all tables
    print("--- TABLES ---")
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
    for row in cur.fetchall():
        print(row[0])
        
    print("\n--- SCHEMA: student_skills ---")
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, column_default, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'student_skills' 
        ORDER BY ordinal_position;
    """)
    for row in cur.fetchall():
        print(f"{row[0]:<20} | {row[1]:<20} | len: {row[2]} | default: {row[3]} | null: {row[4]}")

    print("\n--- SCHEMA: skill_gaps ---")
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, column_default, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'skill_gaps' 
        ORDER BY ordinal_position;
    """)
    for row in cur.fetchall():
        print(f"{row[0]:<20} | {row[1]:<20} | len: {row[2]} | default: {row[3]} | null: {row[4]}")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
