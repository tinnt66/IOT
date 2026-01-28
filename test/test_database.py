"""
Database Tests
Test suite for database functionality
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Database, RS485Sample, ADXLBatch


def test_rs485_samples():
    """Test RS485 sample CRUD operations"""
    print("\n" + "=" * 60)
    print("Testing RS485 Samples")
    print("=" * 60)
    
    db = Database()
    
    # Test Create
    print("\n1. Creating RS485 sample...")
    sample = RS485Sample(
        time_local=datetime.now().isoformat(),
        temp_c=25.5,
        hum_pct=65.2,
        wind_dir_deg=180,
        wind_dir_txt="South",
        wind_spd_ms=3.5
    )
    sample_id = db.rs485_samples.create(sample)
    print(f"   ✓ Created sample with ID: {sample_id}")
    assert sample_id > 0, "Sample ID should be positive"
    
    # Test Read
    print("\n2. Reading RS485 sample...")
    retrieved = db.rs485_samples.get_by_id(sample_id)
    assert retrieved is not None, "Sample should exist"
    print(f"   ✓ Retrieved: {retrieved}")
    print(f"     Temperature: {retrieved.temp_c}°C")
    print(f"     Humidity: {retrieved.hum_pct}%")
    
    # Test Get Latest
    print("\n3. Getting latest RS485 samples...")
    latest = db.rs485_samples.get_latest(limit=5)
    print(f"   ✓ Found {len(latest)} latest samples")
    assert len(latest) > 0, "Should have at least one sample"
    
    # Test Update
    print("\n4. Updating RS485 sample...")
    updated = db.rs485_samples.update(sample_id, temp_c=26.0, hum_pct=64.5)
    assert updated, "Update should succeed"
    retrieved = db.rs485_samples.get_by_id(sample_id)
    print(f"   ✓ Updated temperature to: {retrieved.temp_c}°C")
    assert retrieved.temp_c == 26.0, "Temperature should be updated"
    
    # Test Count
    print("\n5. Counting RS485 samples...")
    count = db.rs485_samples.count()
    print(f"   ✓ Total samples: {count}")
    assert count > 0, "Should have samples in database"
    
    print("\n✅ All RS485 sample tests passed!")


def test_adxl_batches():
    """Test ADXL batch CRUD operations"""
    print("\n" + "=" * 60)
    print("Testing ADXL Batches")
    print("=" * 60)
    
    db = Database()
    
    # Test Create
    print("\n1. Creating ADXL batch...")
    batch = ADXLBatch(
        chunk_start_us=1609459200000000,
        samples={
            "x": [1.2, 1.3, 1.4],
            "y": [0.5, 0.6, 0.7],
            "z": [9.8, 9.9, 10.0]
        }
    )
    batch_id = db.adxl_batches.create(batch)
    print(f"   ✓ Created batch with ID: {batch_id}")
    assert batch_id > 0, "Batch ID should be positive"
    
    # Test Read
    print("\n2. Reading ADXL batch...")
    retrieved_batch = db.adxl_batches.get_by_id(batch_id)
    assert retrieved_batch is not None, "Batch should exist"
    print(f"   ✓ Retrieved: {retrieved_batch}")
    print(f"     Samples: {retrieved_batch.samples}")
    
    # Test Get Latest
    print("\n3. Getting latest ADXL batches...")
    latest = db.adxl_batches.get_latest(limit=5)
    print(f"   ✓ Found {len(latest)} latest batches")
    assert len(latest) > 0, "Should have at least one batch"
    
    # Test Get by Chunk Start
    print("\n4. Getting batch by chunk start...")
    found_batch = db.adxl_batches.get_by_chunk_start(1609459200000000)
    assert found_batch is not None, "Should find batch by chunk start"
    print(f"   ✓ Found batch: {found_batch}")
    
    # Test Count
    print("\n5. Counting ADXL batches...")
    count = db.adxl_batches.count()
    print(f"   ✓ Total batches: {count}")
    assert count > 0, "Should have batches in database"
    
    print("\n✅ All ADXL batch tests passed!")


def test_database_initialization():
    """Test database initialization"""
    print("\n" + "=" * 60)
    print("Testing Database Initialization")
    print("=" * 60)
    
    db = Database()
    print("   ✓ Database initialized successfully")
    
    # Test that tables exist by querying counts
    rs485_count = db.rs485_samples.count()
    adxl_count = db.adxl_batches.count()
    
    print(f"   ✓ RS485 samples table: {rs485_count} records")
    print(f"   ✓ ADXL batches table: {adxl_count} records")
    
    print("\n✅ Database initialization test passed!")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("SQLite Database Test Suite")
    print("=" * 60)
    
    try:
        test_database_initialization()
        test_rs485_samples()
        test_adxl_batches()
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed successfully!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
