# IoT Sensor Data Collection System

Hệ thống thu thập và quản lý dữ liệu từ cảm biến IoT với **Real-time Dashboard**.

## 🌟 Key Features

✅ **REST API** - Nhận dữ liệu từ IoT sensors  
✅ **Real-time Dashboard** - WebSocket broadcast tức thì  
✅ **SQLite Database** - Lưu trữ dữ liệu lâu dài  
✅ **Modern UI** - Dark theme responsive dashboard

## 📁 Cấu trúc Project

```
d:\IOT/
├── init_database.py      # 🚀 Initialize database
├── run_api_server.py     # 🚀 Run Flask server + Dashboard
├── start_api_server.bat  # 🚀 Quick start (Windows)
│
├── .env                  # 🔧 Single configuration file
├── .env.example         # 🔧 Configuration template
│
├── database/             # 📦 SQLite ORM Library
│   ├── connect.py
│   ├── models.py
│   └── functions.py
│
├── rest-api/             # 📦 Flask + SocketIO Library
│   ├── app.py           # Main Flask application
│   ├── templates/       # HTML dashboard
│   │   └── index.html
│   └── static/          # CSS, JS
│       ├── css/style.css
│       └── js/dashboard.js
│
├── test/                 # 🧪 Test Suites
│   ├── test_database.py
│   └── test_api.py
│
└── old/                  # 📂 Legacy code
    └── rs485_adxl345.py # Raspberry Pi sensor reader
```

## 🚀 Quick Start

### 1. Cài đặt

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r rest-api\requirements.txt
```

### 2. Khởi tạo Database

```bash
python init_database.py
```

### 3. Chạy Server + Dashboard

**Cách 1: Batch script**
```bash
start_api_server.bat
```

**Cách 2: Python script**
```bash
python run_api_server.py
```

### 4. Mở Dashboard

Browser: **http://localhost:8000/**

Dashboard sẽ tự động update real-time khi có dữ liệu mới!

## 📊 Data Flow

```
Raspberry Pi (Sensors)
    ├─ RS485: Temp/Humidity/Wind (1Hz)
    └─ ADXL345: Accelerometer (500Hz)
         │
         │ HTTP POST /ingest
         ▼
    Flask Server (Windows)
         ├─ [1] Lưu vào SQLite Database
         └─ [2] Broadcast qua WebSocket
                    ▼
            Browser Dashboard
            (Realtime Update)
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Real-time Dashboard (HTML) |
| GET | `/api` | API information |
| GET | `/health` | Health check + stats |
| POST | `/ingest` | Receive sensor data 🔐 |

**🔐 = Requires API Key**

### POST /ingest Example

```bash
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: iotserver" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "raspi-01",
    "ts": "2026-01-28T08:00:00Z",
    "type": "rs485",
    "sample": {
      "time_local": "2026-01-28 15:00:00",
      "temp_c": 25.5,
      "hum_pct": 65.2
    }
  }'
```

**Dashboard sẽ tự động cập nhật ngay lập tức!**

## 🎨 Dashboard Features

### Real-time Monitoring
- 🌡️ **Temperature** - Nhiệt độ (°C)
- 💧 **Humidity** - Độ ẩm (%)
- 🧭 **Wind Direction** - Hướng gió
- 💨 **Wind Speed** - Tốc độ gió (m/s)
- 📈 **ADXL Batches** - Dữ liệu rung động

### Connection Status
- 🟢 **Connected** - WebSocket active
- 🔴 **Disconnected** - Connection lost

### Activity Log
- Realtime event logging
- Color-coded by data type
- Auto-scroll latest

### Statistics
- Total RS485 samples
- Total ADXL batches
- Last update timestamp

## 🔄 WebSocket Integration

### Client (JavaScript)

```javascript
// Auto-connect to server
const socket = io();

// Listen for RS485 data
socket.on('rs485_data', (data) => {
    console.log('New RS485:', data);
    updateDashboard(data);
});

// Listen for ADXL data
socket.on('adxl_data', (data) => {
    console.log('New ADXL:', data);
    updateBatch(data);
});
```

### Server (Python)

```python
# Broadcast to all connected clients
socketio.emit('rs485_data', {
    'device_id': device_id,
    'data': sample_data
}, namespace='/')
```

## 💾 Database Schema

### `rs485_samples`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary Key |
| time_local | TEXT | Timestamp |
| temp_c | REAL | Temperature (°C) |
| hum_pct | REAL | Humidity (%) |
| wind_dir_deg | INTEGER | Wind direction (°) |
| wind_dir_txt | TEXT | Wind direction text |
| wind_spd_ms | REAL | Wind speed (m/s) |
| created_at | TEXT | Record creation |

### `adxl_batches`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary Key |
| chunk_start_us | INTEGER | Timestamp (μs) |
| samples | TEXT (JSON) | Sensor data array |
| created_at | TEXT | Record creation |

## 🔧 Configuration (.env)

**Single file tại root:**

```bash
# Database
DB_PATH=sensors.db

# REST API
API_KEY=iotserver
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False

# CORS
ALLOW_ORIGINS=*

# General
LOG_LEVEL=INFO
TIMEZONE=Asia/Ho_Chi_Minh
```

## 🧪 Testing

### Database Test
```bash
python test\test_database.py
```

### API Test
```bash
# Start server first
python run_api_server.py

# In another terminal
python test\test_api.py
```

### Dashboard Test
1. Start server: `python run_api_server.py`
2. Open browser: http://localhost:8000/
3. POST data via API
4. Watch dashboard update realtime! 🎉

## 📦 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Flask 3.0.0 |
| **WebSocket** | Flask-SocketIO 5.3.5 |
| **Database** | SQLite3 |
| **Frontend** | HTML5 + CSS3 + JavaScript |
| **Validation** | Pydantic 2.5.3 |
| **CORS** | Flask-CORS 4.0.0 |

## 🔐 Security

- ✅ API Key authentication (X-API-Key header)
- ✅ CORS configuration
- ✅ Input validation (Pydantic)
- ✅ SQL injection protection (parameterized queries)

## 🐛 Troubleshooting

### Dashboard không kết nối
```
- Kiểm tra server đang chạy
- Check browser console (F12)
- Verify CORS settings trong .env
```

### Data không hiển thị realtime
```
- Verify API key đúng
- Check POST request format
- Xem server logs
```

### Port đã bị sử dụng
```bash
# Đổi port trong .env
API_PORT=8001
```

## 📚 Documentation

- **Project README**: `README.md` (this file)
- **API README**: `rest-api/README.md`
- **Quick Start**: `QUICKSTART.md`

## 🎯 Use Cases

1. **Real-time Monitoring** - Dashboard hiển thị sensor data tức thì
2. **Data Logging** - Lưu lịch sử dài hạn vào database
3. **Remote Monitoring** - Access dashboard từ bất kỳ đâu
4. **Data Analysis** - Query database để phân tích trends

## 📝 Changelog

### v2.0.0 (2026-01-28) - Current
- ✅ Migrated from FastAPI to Flask
- ✅ Added WebSocket support (SocketIO)
- ✅ Created real-time dashboard UI
- ✅ Auto-broadcast on data ingest
- ✅ Modern dark theme design

### v1.0.0
- Initial implementation with FastAPI
- Database package structure
- Basic REST endpoints

---

**Author**: Your Team  
**Updated**: 2026-01-28  
**Version**: 2.0.0  
**Stack**: Flask + SocketIO + SQLite + WebSocket
