"""
Database Initialization Script
Run this to create/initialize the SQLite database with tables and indexes
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import Database


def main():
    """Initialize database"""
    print("=" * 60)
    print("Database Initialization")
    print("=" * 60)
    
    # Create database instance (auto-initializes)
    db = Database()
    
    print(f"\n✓ Database initialized successfully!")
    print(f"  Location: {db.connection.db_path}")
    
    # Show statistics
    print(f"\n📊 Current Statistics:")
    print(f"  RS485 samples: {db.rs485_samples.count()}")
    print(f"  ADXL batches:  {db.adxl_batches.count()}")
    
    print("\n" + "=" * 60)
    print("✅ Database ready to use!")
    print("=" * 60)


if __name__ == "__main__":
    main()
