import sys
import traceback

try:
    from migrations.data.m_001_initial import InitialMigration
    print("SUCCESS: Module imported")
    print(f"Migration version: {InitialMigration.version}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()
