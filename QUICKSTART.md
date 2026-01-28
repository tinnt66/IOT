# Quick Reference - IoT Sensor System v2.0

## 🚀 Start Server + Dashboard

```bash
# Quick start (Windows)
start_api_server.bat

# Or Python
python run_api_server.py
```

**Dashboard**: http://localhost:8000/  
**Status**: Connection indicator (🟢 = Connected)

## 📊 Architecture

```
┌─────────────────┐
│  Raspberry Pi   │
│                 │
│ RS485: 1Hz      │── POST /ingest ──┐
│ ADXL: 500Hz     │                  │
└─────────────────┘                  ▼
                            ┌──────────────────┐
                            │  Flask Server    │
                            │                  │
                            │  [1] Save to DB  │
                            │  [2] Broadcast   │
                            └────────┬─────────┘
                                     │ WebSocket
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
              ┌─────────┐      ┌─────────┐    ┌─────────┐
              │ Browser │      │ Browser │    │ Browser │
              │ Client  │      │ Client  │    │ Client  │
              └─────────┘      └─────────┘    └─────────┘
                  (Realtime Update - No Refresh Needed)
```

## 🔌 API Usage

### Send RS485 Data
```bash
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: iotserver" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "raspi-01",
    "ts": "2026-01-28T08:00:00Z",
    "type": "rs485",
    "sample": {
      "temp_c": 25.5,
      "hum_pct": 65.2
    }
  }'
```

**→ Dashboard updates instantly! 🎉**

### Health Check
```bash
curl http://localhost:8000/health
```

## 🎨 Dashboard Features

| Feature | Description |
|---------|-------------|
| 🌡️ Temperature | Real-time °C |
| 💧 Humidity | Real-time % |
| 🧭 Wind Dir | Direction + degrees |
| 💨 Wind Speed | m/s |
| 📈 ADXL Batches | Sample count + freq |
| 📋 Activity Log | Recent events |
| 🟢 Connection | WebSocket status |

## 🔄 WebSocket Events

### Server → Client

```javascript
// Connection established
socket.on('connection_response', data => { ... })

// New RS485 data
socket.on('rs485_data', data => {
    // Update UI automatically
})

// New ADXL batch
socket.on('adxl_data', data => {
    // Update UI automatically
})

// Statistics update
socket.on('stats_update', data => { ... })
```

### Client → Server

```javascript
// Request current stats
socket.emit('request_stats')
```

## 💾 Database Access

```python
from database import Database

db = Database()

# Get latest
latest = db.rs485_samples.get_latest(10)

# Count
print(f"Total: {db.rs485_samples.count()}")
```

## 🔧 Configuration (.env)

```bash
# API
API_KEY=iotserver
API_HOST=0.0.0.0
API_PORT=8000

# Database
DB_PATH=sensors.db

# CORS
ALLOW_ORIGINS=*
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `run_api_server.py` | Start Flask + SocketIO |
| `init_database.py` | Initialize database |
| `.env` | All configuration |
| `rest-api/app.py` | Flask application |
| `rest-api/templates/index.html` | Dashboard UI |
| `rest-api/static/` | CSS, JS files |

## 🧪 Test Workflow

```bash
# 1. Start server
python run_api_server.py

# 2. Open dashboard
http://localhost:8000/

# 3. Send test data
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: iotserver" \
  -d '...'

# 4. Watch dashboard update! 🎯
```

## 🐛 Troubleshooting

**Dashboard không kết nối**
```
→ Check server running
→ Check browser console (F12)
→ Verify ALLOW_ORIGINS in .env
```

**Data không update**
```
→ Verify API key
→ Check POST format
→ View server logs
```

**Port bị chiếm**
```bash
# Change in .env
API_PORT=8001
```

## 🎯 Quick Test

```bash
# Terminal 1: Start server
python run_api_server.py

# Terminal 2: Send data
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: iotserver" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test","ts":"2026-01-28T08:00:00Z","type":"rs485","sample":{"temp_c":25.5,"hum_pct":65.2}}'

# Browser: http://localhost:8000/
# → See realtime update! ✨
```

## 📊 Tech Stack

**Backend**: Flask 3.0 + SocketIO 5.3  
**Frontend**: HTML5 + CSS3 + JS  
**Database**: SQLite3  
**WebSocket**: Socket.IO  

---
**Version**: 2.0.0 | **Updated**: 2026-01-28  
**Key**: Realtime Dashboard với WebSocket
