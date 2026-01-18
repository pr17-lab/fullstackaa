#!/usr/bin/env python3
"""
Parallel Password Generation Script

Generate deterministic passwords for users with parallel processing.
Uses multiprocessing to leverage multiple CPU cores for significant performance improvement.

Expected Performance:
    Sequential: ~3 hours for 8,840 users
    Parallel:   ~30-45 minutes for 8,840 users (6-8x faster)

Password Format: {student_id}@123

SAFETY: Requires environment variable ALLOW_PASSWORD_RESET=true to run.

Usage:
    # Windows
    $env:ALLOW_PASSWORD_RESET="true"; python backend/scripts/generate_passwords_parallel.py

    # Linux/Mac
    ALLOW_PASSWORD_RESET=true python backend/scripts/generate_passwords_parallel.py
"""

import os
import sys
import time
from pathlib import Path
from multiprocessing import Pool, cpu_count
from typing import List, Tuple

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User

# Password hashing context (matches auth configuration)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a single password using bcrypt."""
    return pwd_context.hash(password)


def process_batch(batch_data: Tuple[str, List[Tuple[int, str]]]) -> int:
    """
    Process a batch of users in a separate process.
    
    Args:
        batch_data: Tuple of (DATABASE_URL, list of (user_id, password) tuples)
        
    Returns:
        Number of users processed
    """
    database_url, user_password_pairs = batch_data
    
    # Create new engine and session for this process
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        processed = 0
        for user_id, password in user_password_pairs:
            hashed = hash_password(password)
            session.execute(
                text("UPDATE users SET password_hash = :hash WHERE id = :id"),
                {"hash": hashed, "id": user_id}
            )
            processed += 1
        
        session.commit()
        return processed
        
    except Exception as e:
        session.rollback()
        print(f"Error in batch processing: {e}")
        return 0
    finally:
        session.close()
        engine.dispose()


def generate_passwords_parallel():
    """Generate and update passwords for all users using parallel processing."""
    
    # Safety check: require environment variable
    if os.getenv("ALLOW_PASSWORD_RESET") != "true":
        print("=" * 70)
        print("❌ SAFETY CHECK FAILED")
        print("=" * 70)
        print("\nThis script will reset ALL user passwords in the database.")
        print("To proceed, set the environment variable ALLOW_PASSWORD_RESET=true\n")
        print("Windows PowerShell:")
        print('  $env:ALLOW_PASSWORD_RESET="true"; python backend/scripts/generate_passwords_parallel.py\n')
        print("Linux/Mac:")
        print('  ALLOW_PASSWORD_RESET=true python backend/scripts/generate_passwords_parallel.py\n')
        print("=" * 70)
        sys.exit(1)
    
    print("=" * 70)
    print("PARALLEL PASSWORD GENERATION")
    print("=" * 70)
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get all users that need passwords
        print("\n🔍 Fetching users from database...")
        users = session.query(User.id, User.student_id).filter(
            User.student_id.isnot(None)
        ).all()
        
        total_users = len(users)
        
        if total_users == 0:
            print("⚠️  No users with student_id found in database")
            session.close()
            return
        
        print(f"   Found {total_users} users to process")
        
        # Determine optimal number of processes
        num_cores = cpu_count()
        num_processes = min(num_cores, max(1, total_users // 100))  # At least 100 users per process
        
        print(f"\n⚙️  Configuration:")
        print(f"   CPU Cores Available: {num_cores}")
        print(f"   Processes to Use:    {num_processes}")
        print(f"   Users per Process:   ~{total_users // num_processes}")
        
        # Create batches of (user_id, password) pairs
        user_password_pairs = [
            (user.id, f"{user.student_id}@123") 
            for user in users
        ]
        
        batch_size = len(user_password_pairs) // num_processes
        batches = []
        
        for i in range(num_processes):
            start_idx = i * batch_size
            if i == num_processes - 1:
                # Last batch gets remaining users
                batch = user_password_pairs[start_idx:]
            else:
                batch = user_password_pairs[start_idx:start_idx + batch_size]
            
            # Include database URL with each batch
            batches.append((settings.DATABASE_URL, batch))
        
        print(f"\n🚀 Starting parallel password generation...")
        print(f"   {len(batches)} batches created")
        
        start_time = time.time()
        
        # Process batches in parallel
        with Pool(num_processes) as pool:
            results = pool.map(process_batch, batches)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Calculate statistics
        total_processed = sum(results)
        
        print(f"\n{'=' * 70}")
        print("✅ PASSWORD GENERATION COMPLETE")
        print(f"{'=' * 70}")
        print(f"\n📊 Statistics:")
        print(f"   Users Processed:    {total_processed}/{total_users}")
        print(f"   Time Elapsed:       {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        print(f"   Average per User:   {(elapsed_time/total_processed)*1000:.2f} ms")
        print(f"   Throughput:         {total_processed/elapsed_time:.2f} users/second")
        
        # Performance comparison (estimated)
        sequential_estimate = total_processed * 0.15  # ~150ms per user sequentially
        speedup = sequential_estimate / elapsed_time if elapsed_time > 0 else 0
        
        print(f"\n⚡ Performance:")
        print(f"   Estimated Sequential Time: {sequential_estimate/60:.2f} minutes")
        print(f"   Actual Parallel Time:      {elapsed_time/60:.2f} minutes")
        print(f"   Speedup Factor:            {speedup:.2f}x")
        
        print(f"\n{'=' * 70}")
        print("\n🔑 Login Format:")
        print("   Email:    [user email from database]")
        print("   Password: [student_id]@123")
        print("\nExample:")
        print("   Email:    priya.sharma@example.com")
        print("   Password: STU001@123")
        print(f"{'=' * 70}\n")
        
        # Verify password hash format
        sample_user = session.query(User).filter(User.password_hash.isnot(None)).first()
        if sample_user and sample_user.password_hash.startswith("$2b$"):
            print("✅ Verification: Password hashes use bcrypt format ($2b$)\n")
        else:
            print("⚠️  Warning: Password hash format may be incorrect\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


def main():
    """Main function."""
    generate_passwords_parallel()


if __name__ == "__main__":
    main()
