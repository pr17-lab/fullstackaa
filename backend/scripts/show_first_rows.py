"""
Script to display the first 3 rows from all tables in the database.
"""
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect, text
from app.core.config import settings

def show_first_rows(output_file=None):
    engine = create_engine(settings.DATABASE_URL)
    
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    
    print(f"\n{'='*80}")
    print(f"Found {len(table_names)} tables in the database")
    print(f"{'='*80}\n")
    
    with engine.connect() as conn:
        for table_name in sorted(table_names):
            print(f"\n{'─'*80}")
            print(f"TABLE: {table_name}")
            print(f"{'─'*80}")
            
            # Get column names
            columns = inspector.get_columns(table_name)
            column_names = [col['name'] for col in columns]
            
            # Query first 3 rows
            result = conn.execute(text(f'SELECT * FROM "{table_name}" LIMIT 3'))
            rows = result.fetchall()
            
            if not rows:
                print("  (empty table)")
            else:
                # Print header
                print("\n  " + " | ".join(column_names))
                print("  " + "-" * (sum(len(col) for col in column_names) + 3 * len(column_names)))
                
                # Print rows
                for row in rows:
                    row_data = []
                    for value in row:
                        if value is None:
                            row_data.append("NULL")
                        elif isinstance(value, str) and len(value) > 30:
                            row_data.append(value[:27] + "...")
                        else:
                            row_data.append(str(value))
                    print("  " + " | ".join(row_data))
            
            print()
    
    print(f"{'='*80}\n")
    
    if output_file:
        print(f"\n✓ Output saved to: {output_file}")

if __name__ == "__main__":
    output_file = Path(__file__).parent / "table_preview.txt"
    
    # Redirect stdout to file
    import io
    output_buffer = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = output_buffer
    
    try:
        show_first_rows(output_file)
        
        # Get the output
        output_content = output_buffer.getvalue()
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_content)
        
        # Also print to console
        sys.stdout = original_stdout
        print(output_content)
        print(f"\n✓ Output also saved to: {output_file}")
        
    finally:
        sys.stdout = original_stdout
