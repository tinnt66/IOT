# IoT Sensor Data REST API + Real-time Dashboard

Flask server với SocketIO để nhận dữ liệu từ cảm biến IoT và hiển thị real-time trên dashboard.

## 🌟 Features

✅ **REST API** - POST /ingest để nhận dữ liệu  
✅ **Real-time Dashboard** - WebSocket broadcast tức thì  
✅ **Database Storage** - Lưu vào SQLite  
✅ **Modern UI** - Dark theme responsive dashboard

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python run_api_server.py

# Or use batch file
start_api_server.bat
```

Server khởi động tại:
- **Dashboard**: http://localhost:8000/
- **API Info**: http://localhost:8000/api
- **Health Check**: http://localhost:8000/health

## 📊 Architecture

```
Raspberry Pi → POST /ingest → Flask Server
                                    ↓
                    [1] Lưu vào Database (SQLite)
                    [2] Broadcast qua WebSocket
                                    ↓
                            Browser Dashboard
                            (Realtime Update)
```

## 🔌 API Endpoints

### **POST /ingest**
Nhận dữ liệu từ IoT sensors

**Headers:**
```http
X-API-Key: iotserver
Content-Type: application/json
```

**RS485 Request:**
```json
{
  "device_id": "raspi-01",
  "ts": "2026-01-28T08:00:00Z",
  "type": "rs485",
  "sample": {
    "time_local": "2026-01-28 15:00:00",
    "temp_c": 25.5,
    "hum_pct": 65.2,
    "wind_dir_deg": 180,
    "wind_dir_txt": "S",
    "wind_spd_ms": 3.5
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "RS485 sample stored with ID 123",
  "device_id": "raspi-01",
  "timestamp": "2026-01-28T08:00:00Z",
  "records_created": 1
}
```

### **GET /**
Serve HTML dashboard với WebSocket

### **GET /health**
Health check + database stats

## 🔄 WebSocket Events

### Client → Server

**`connect`** - Kết nối mới
```javascript
socket.on('connect', () => {
    console.log('Connected');
});
```

**`request_stats`** - Yêu cầu statistics
```javascript
socket.emit('request_stats');
```

### Server → Client

**`connection_response`** - Xác nhận kết nối
```javascript
{
  "status": "connected",
  "message": "Welcome to IoT Dashboard",
  "timestamp": "2026-01-28T15:00:00"
}
```

**`rs485_data`** - Dữ liệu RS485 mới
```javascript
{
  "device_id": "raspi-01",
  "timestamp": "2026-01-28T08:00:00Z",
  "data": {
    "temp_c": 25.5,
    "hum_pct": 65.2,
    ...
  },
  "id": 123
}
```

**`adxl_data`** - Dữ liệu ADXL batch mới
```javascript
{
  "device_id": "raspi-01",
  "chunk_start_us": 1609459200000000,
  "sample_count": 50,
  "fs_hz": 500,
  "id": 45
}
```

**`stats_update`** - Cập nhật statistics
```javascript
{
  "rs485_count": 1234,
  "adxl_count": 567,
  "timestamp": "2026-01-28T15:00:00"
}
```

## 🏗️ Project Structure

```
rest-api/
├── app.py               # Flask + SocketIO application
├── config.py            # Configuration
├── middleware.py        # API Key auth
├── schemas.py           # Pydantic models
├── routes/              # (Legacy - merged into app.py)
├── templates/           # HTML templates
│   └── index.html      # Dashboard UI
├── static/              # Static files
│   ├── css/
│   │   └── style.css   # Dashboard styles
│   └── js/
│       └── dashboard.js # WebSocket client
└── requirements.txt     # Dependencies
```

## 🎨 Dashboard Features

### Real-time Display
- 🌡️ Temperature
- 💧 Humidity  
- 🧭 Wind Direction
- 💨 Wind Speed
- 📈 ADXL Accelerometer batches

### Activity Log
- Tự động scroll
- Màu theo loại data (RS485/ADXL)
- Timestamp mỗi event

### Statistics
- Total RS485 samples
- Total ADXL batches
- Last update time

## 🧪 Testing

### Test API với curl

```bash
# RS485 data
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: iotserver" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test",
    "ts": "2026-01-28T08:00:00Z",
    "type": "rs485",
    "sample": {
      "time_local": "2026-01-28 15:00:00",
      "temp_c": 25.5,
      "hum_pct": 65.2
    }
  }'
```

### Test Dashboard

1. Mở browser: http://localhost:8000/
2. Kiểm tra connection status (green dot)
3. POST data qua API
4. Dashboard tự động update realtime

## 📦 Dependencies

```
flask==3.0.0
flask-cors==4.0.0
flask-socketio==5.3.5
python-socketio==5.10.0
python-dotenv==1.0.0
pydantic==2.5.3
```

## 🔐 Security

- ✅ API Key authentication (X-API-Key header)
- ✅ CORS configuration
- ✅ Input validation (Pydantic)
- ✅ SQL injection protection

## 🔧 Configuration

Đọc từ `.env` tại project root:

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

## 🐛 Troubleshooting

### WebSocket not connecting
- Check browser console for errors
- Verify CORS settings in .env
- Make sure server is running

### Data không update
- Check API key
- Verify POST request format
- Check server logs

### Port already in use
```bash
# Change in .env
API_PORT=8001
```

## 📝 Changelog

### v2.0.0 (Current)
- ✅ Migrated from FastAPI to Flask
- ✅ Added WebSocket support (SocketIO)
- ✅ Created real-time dashboard
- ✅ Auto-broadcast on data ingest

### v1.0.0
- Initial FastAPI implementation
- Basic REST endpoints

---

**Stack**: Flask + SocketIO + SQLite + WebSocket  
**Updated**: 2026-01-28
