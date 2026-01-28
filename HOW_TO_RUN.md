# 🚀 Cách chạy Server

## Quick Start

```bash
# 1. Activate virtual environment
.venv\Scripts\activate

# 2. Run server
python run_api_server.py
```

Server khởi động tại: **http://localhost:8000/**

## Dashboard

Mở browser: http://localhost:8000/

**Features:**
- 🟢 Connection status (realtime)
- 🌡️ Temperature tile
- 💧 Humidity tile  
- 🧭 Wind direction tile
- 💨 Wind speed tile
- 📈 ADXL batch info
- 📋 Activity log

## Test API

```bash
# Terminal mới (keep server running)
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: iotserver" \
  -H "Content-Type: application/json" \
  -d "{\"device_id\":\"test\",\"ts\":\"2026-01-28T08:00:00Z\",\"type\":\"rs485\",\"sample\":{\"temp_c\":25.5,\"hum_pct\":65.2}}"
```

**→ Dashboard sẽ update tức thì!** 🎉

## Troubleshooting

### "No module named flask"
```bash
# Bạn chưa activate venv
.venv\Scripts\activate
```

### Port 8000 đã bị dùng
```bash
# Đổi port trong .env
API_PORT=8001
```

### WebSocket không kết nối
```
- Check server đang chạy
- F12 browser console xem lỗi
- Verify ALLOW_ORIGINS trong .env
```

## Commands Summary

```bash
# Activate venv
.venv\Scripts\activate

# Run server
python run_api_server.py

# Or use batch file
start_api_server.bat

# Test health
curl http://localhost:8000/health

# View API info
curl http://localhost:8000/api
```

---
**Important**: Luôn activate venv trước khi chạy!
