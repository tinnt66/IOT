"""
Test REST API Endpoints
Run this after starting the server (python run_api_server.py)
"""

import requests
import json
from datetime import datetime


# Configuration
BASE_URL = "http://127.0.0.1:8080"
API_KEY = "iotserver"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}


def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("TEST: Health Check")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed!")


def test_root():
    """Test root endpoint"""
    print("\n" + "="*60)
    print("TEST: Root Endpoint")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✅ Root endpoint passed!")


def test_rs485_ingest():
    """Test RS485 data ingestion"""
    print("\n" + "="*60)
    print("TEST: RS485 Data Ingestion")
    print("="*60)
    
    data = {
        "device_id": "test-raspi-01",
        "ts": datetime.now().isoformat() + "Z",
        "type": "rs485",
        "sample": {
            "time_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temp_c": 25.5,
            "hum_pct": 65.2,
            "wind_dir_deg": 180,
            "wind_dir_txt": "S",
            "wind_spd_ms": 3.5
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/ingest",
        headers=HEADERS,
        json=data
    )
    
    print(f"Request: {json.dumps(data, indent=2)}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 202
    assert response.json()["status"] == "success"
    print("✅ RS485 ingestion passed!")


def test_adxl_batch_ingest():
    """Test ADXL batch data ingestion"""
    print("\n" + "="*60)
    print("TEST: ADXL Batch Data Ingestion")
    print("="*60)
    
    # Generate sample data (simulate 50 samples at 500Hz)
    samples = [[i, i+100, i+200] for i in range(50)]
    
    data = {
        "device_id": "test-raspi-01",
        "ts": datetime.now().isoformat() + "Z",
        "type": "adxl_batch",
        "fs_hz": 500,
        "chunk_start_us": int(datetime.now().timestamp() * 1_000_000),
        "samples": samples
    }
    
    response = requests.post(
        f"{BASE_URL}/ingest",
        headers=HEADERS,
        json=data
    )
    
    print(f"Samples count: {len(samples)}")
    print(f"First 3 samples: {samples[:3]}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 202
    assert response.json()["status"] == "success"
    assert response.json()["records_created"] == 50
    print("✅ ADXL batch ingestion passed!")


def test_invalid_api_key():
    """Test with invalid API key"""
    print("\n" + "="*60)
    print("TEST: Invalid API Key")
    print("="*60)
    
    bad_headers = {
        "X-API-Key": "wrong-key",
        "Content-Type": "application/json"
    }
    
    data = {
        "device_id": "test-device",
        "ts": datetime.now().isoformat() + "Z",
        "type": "rs485",
        "sample": {"time_local": "2026-01-28 15:00:00"}
    }
    
    response = requests.post(
        f"{BASE_URL}/ingest",
        headers=bad_headers,
        json=data
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 401
    print("✅ Invalid API key test passed!")


def test_missing_api_key():
    """Test without API key"""
    print("\n" + "="*60)
    print("TEST: Missing API Key")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/ingest",
        headers={"Content-Type": "application/json"},
        json={"device_id": "test", "type": "rs485"}
    )
    
    print(f"Status Code: {response.status_code}")
    
    assert response.status_code in [401, 403, 422]  # Could be any of these
    print("✅ Missing API key test passed!")


def main():
    """Run all tests"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*10 + "REST API TEST SUITE" + " "*29 + "║")
    print("╚" + "="*58 + "╝")
    print(f"\nTesting server at: {BASE_URL}")
    print(f"Using API Key: {API_KEY}")
    
    try:
        # Test basic endpoints
        test_root()
        test_health()
        
        # Test data ingestion
        test_rs485_ingest()
        test_adxl_batch_ingest()
        
        # Test security
        test_invalid_api_key()
        test_missing_api_key()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n" + "="*60)
        print("❌ ERROR: Cannot connect to server")
        print("="*60)
        print("\nPlease start the server first:")
        print("  python run_api_server.py")
        print("\nOr run: start_api_server.bat")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
