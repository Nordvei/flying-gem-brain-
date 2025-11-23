# Edge Node

The edge node runs on each drone's Raspberry Pi 5 and provides:

- **Autonomous Operation** - Makes local decisions without constant ground link
- **Object Detection** - YOLOv8n inference at 30 FPS using Hailo AI HAT+
- **Flight Control** - MAVLink communication with Pixhawk 4
- **Mesh Communication** - NATS pub/sub for swarm coordination
- **Pattern Federation** - Shares detections via PostgreSQL

---

## Hardware Requirements

- **Raspberry Pi 5** (8GB recommended)
- **Hailo AI HAT+** (26 TOPS NPU)
- **Raspberry Pi Camera v3** (12MP, autofocus)
- **Pixhawk 4** flight controller
- **MicroSD Card** (64GB+, Class 10)
- **USB-C Power** (5V 5A for Pi 5 + Hailo)

---

## Software Setup

### 1. Install Raspberry Pi OS

```bash
# Use Raspberry Pi Imager
# Choose: Raspberry Pi OS (64-bit)
# Enable SSH in advanced settings
```

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+
sudo apt install python3 python3-pip python3-venv -y

# Install system libraries
sudo apt install libcamera-dev libopencv-dev -y

# Create virtual environment
python3 -m venv ~/edge-venv
source ~/edge-venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

### 3. Install Hailo SDK

```bash
# Download Hailo SDK from https://hailo.ai/developer-zone/
# (Requires free developer account)

# Install HailoRT
wget https://hailo.ai/downloads/hailort-4.17.0-linux-aarch64.deb
sudo dpkg -i hailort-4.17.0-linux-aarch64.deb

# Verify installation
hailortcli fw-control identify
```

### 4. Compile YOLOv8n for Hailo

```bash
# Download Hailo Model Zoo
git clone https://github.com/hailo-ai/hailo_model_zoo.git
cd hailo_model_zoo

# Compile YOLOv8n
hailomz compile yolov8n --hw-arch hailo8l --har models/yolov8n.har

# Move compiled model
mkdir -p ~/flying-gem-brain/models
cp yolov8n.hef ~/flying-gem-brain/models/
```

---

## Module Overview

### `edge_node.py`

Main edge node orchestrator. Coordinates all edge components.

**Usage:**
```bash
python edge_node.py --drone-id=drone-1 --nats-url=nats://192.168.1.100:4222
```

**Key Functions:**
- Connects to NATS mesh
- Publishes telemetry (1 Hz)
- Publishes detections (real-time)
- Handles commands (RTL, loiter, waypoint, emergency)
- Manages drone state and battery

### `hailo_detector.py`

YOLOv8n object detection using Hailo AI HAT+.

**Features:**
- 30 FPS inference at 640x640
- 80 COCO classes
- Confidence filtering (default: 0.5)
- Non-max suppression (NMS)
- ~2.5W power consumption

**Example:**
```python
from hailo_detector import HailoDetector

detector = HailoDetector(
    model_path="models/yolov8n.hef",
    confidence_threshold=0.5
)

detections = detector.detect(frame)

for det in detections:
    print(f"{det.class_name}: {det.confidence:.2f} @ {det.bbox}")
```

### `mavlink_bridge.py`

MAVLink communication with Pixhawk 4 flight controller.

**Features:**
- Telemetry streaming (GPS, battery, attitude)
- Flight mode control (GUIDED, RTL, AUTO, LAND)
- Waypoint navigation
- Arm/disarm control
- Emergency procedures

**Example:**
```python
from mavlink_bridge import MAVLinkBridge

bridge = MAVLinkBridge("/dev/ttyACM0")

# Get telemetry
telemetry = bridge.get_telemetry()
print(f"Position: {telemetry.latitude}, {telemetry.longitude}")
print(f"Battery: {telemetry.battery_remaining}%")

# Navigate to waypoint
bridge.goto_waypoint(lat=59.9139, lon=10.7522, alt=100)

# Emergency return
bridge.return_to_launch()
```

---

## NATS Topic Structure

### Published by Edge Node

```python
# Telemetry (1 Hz)
"gem.telemetry.{drone_id}"
{
  "drone_id": "drone-1",
  "timestamp": 1699564800.123,
  "latitude": 59.9139,
  "longitude": 10.7522,
  "altitude": 100.5,
  "battery": 78.5,
  "status": "active"
}

# Detections (real-time)
"gem.detection.{drone_id}"
{
  "drone_id": "drone-1",
  "timestamp": 1699564800.456,
  "object_class": "vehicle",
  "confidence": 0.87,
  "bbox": [100, 150, 200, 180],
  "latitude": 59.9139,
  "longitude": 10.7522
}
```

### Subscribed by Edge Node

```python
# Commands to specific drone
"gem.command.{drone_id}"
{
  "type": "waypoint",
  "waypoint": {"lat": 59.9139, "lon": 10.7522, "alt": 100}
}

# Broadcast commands
"gem.command.broadcast"
{
  "type": "formation_change",
  "formation": "line"
}
```

---

## Configuration

Edge nodes can be configured via environment variables or config file:

**Environment Variables:**
```bash
export DRONE_ID="drone-1"
export NATS_URL="nats://192.168.1.100:4222"
export MAVLINK_PORT="/dev/ttyACM0"
export HAILO_MODEL="models/yolov8n.hef"
export CONFIDENCE_THRESHOLD="0.5"
```

**Config File:** `config.yaml`
```yaml
drone:
  id: "drone-1"
  operator_ratio: 10

nats:
  url: "nats://192.168.1.100:4222"
  reconnect_attempts: 10
  reconnect_delay: 5

mavlink:
  port: "/dev/ttyACM0"
  baud_rate: 57600

hailo:
  model_path: "models/yolov8n.hef"
  confidence_threshold: 0.5
  nms_threshold: 0.45
  input_size: [640, 640]

telemetry:
  publish_rate: 1  # Hz
  detection_rate: 10  # Hz
```

---

## Performance

**Raspberry Pi 5 + Hailo AI HAT+:**

| Metric | Value |
|--------|-------|
| YOLOv8n FPS | ~30 |
| Detection Latency | ~33ms |
| Power Consumption | ~10W total |
| Hailo NPU Power | ~2.5W |
| Memory Usage | ~1.5GB |
| CPU Usage | ~40% |

**Comparison without Hailo (CPU only):**

| Metric | Value |
|--------|-------|
| YOLOv8n FPS | ~2-3 |
| Detection Latency | ~400ms |
| Power Consumption | ~15W |
| CPU Usage | ~100% |

**26 TOPS NPU provides 10-15x speedup over CPU inference**

---

## Troubleshooting

### Hailo Device Not Found

```bash
# Check USB connection
lsusb | grep Hailo

# Should see: "Bus 001 Device 003: ID 1d6b:0003 Hailo AI HAT+"

# Check permissions
sudo usermod -a -G video $USER
# Log out and back in
```

### MAVLink Connection Failed

```bash
# Check USB serial connection
ls -l /dev/ttyACM*

# Should see: /dev/ttyACM0

# Add user to dialout group
sudo usermod -a -G dialout $USER
# Log out and back in

# Test connection manually
mavproxy.py --master=/dev/ttyACM0 --baudrate=57600
```

### NATS Connection Issues

```bash
# Test NATS connection
nats-sub -s nats://192.168.1.100:4222 "gem.>"

# Check firewall
sudo ufw allow 4222/tcp
```

### Camera Not Working

```bash
# Enable camera in raspi-config
sudo raspi-config
# Interface Options → Camera → Enable

# Test camera
libcamera-hello
```

---

## Production Deployment

### Systemd Service

Create `/etc/systemd/system/edge-node.service`:

```ini
[Unit]
Description=Flying GEM Brain Edge Node
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/flying-gem-brain
ExecStart=/home/pi/edge-venv/bin/python edge/edge_node.py --drone-id=drone-1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable edge-node
sudo systemctl start edge-node

# Check status
sudo systemctl status edge-node

# View logs
sudo journalctl -u edge-node -f
```

### Auto-Start on Boot

Add to `/etc/rc.local` (before `exit 0`):

```bash
# Start edge node
/home/pi/edge-venv/bin/python /home/pi/flying-gem-brain/edge/edge_node.py --drone-id=drone-1 > /var/log/edge-node.log 2>&1 &
```

---

## Security Considerations

- **NATS Authentication** - Use tokens for production
- **TLS Encryption** - Enable for NATS mesh
- **Firewall** - Restrict ports (4222 for NATS)
- **SSH Keys** - Disable password authentication
- **Auto-Updates** - Enable unattended security updates

```bash
# Generate NATS auth token
openssl rand -hex 32

# Configure NATS with auth
nats-server -c nats-server.conf
```

**nats-server.conf:**
```
port: 4222
authorization {
  token: "your-generated-token-here"
}
```

---

## Next Steps

1. **Hardware Assembly** - See [../docs/HARDWARE.md](../docs/HARDWARE.md)
2. **Ground Control Setup** - Configure SAGE coordinator
3. **Swarm Testing** - Start with simulation first
4. **Field Testing** - Begin with single drone
5. **Multi-Drone Deployment** - Scale to 5-10 drones

---

**For questions or issues, see [CONTRIBUTING.md](../CONTRIBUTING.md)**
