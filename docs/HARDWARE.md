# Hardware Setup Guide

Complete guide for assembling and configuring Flying GEM Brain hardware.

---

## Bill of Materials (BOM)

### Per Drone (~$1,000 USD)

| Component | Model | Price | Source |
|-----------|-------|-------|--------|
| **Flight Controller** | Pixhawk 4 | $200 | Holybro, Amazon |
| **Compute Module** | Raspberry Pi 5 (8GB) | $80 | Raspberry Pi retailers |
| **AI Accelerator** | Hailo AI HAT+ | $95 | Hailo.ai |
| **Camera** | Raspberry Pi Camera v3 | $25 | Raspberry Pi retailers |
| **GPS** | Ublox NEO-M8N | $30 | Amazon |
| **Telemetry Radio** | SiK Radio 915MHz | $50 | Holybro |
| **Frame** | X650 Quadcopter | $150 | Amazon |
| **Motors** | 4x DJI 2212 920KV | $120 | Amazon |
| **ESCs** | 4x 30A SimonK | $60 | Amazon |
| **Props** | 4x 10x4.5 | $20 | Amazon |
| **Battery** | 6S 5000mAh LiPo | $80 | HobbyKing |
| **Power Module** | PM07 | $15 | Holybro |
| **MicroSD Card** | 64GB Class 10 | $15 | Amazon |
| **Cables/Connectors** | Various | $30 | Amazon |
| **RC Receiver** | FrSky X8R | $30 | Amazon |
| **Total** | | **~$1,000** | |

### Ground Control Station

| Component | Model | Price |
|-----------|-------|-------|
| **Computer** | Any Linux machine | $0-500 |
| **Telemetry Radio** | SiK Radio 915MHz | $50 |
| **RC Transmitter** | FrSky Taranis Q X7 | $120 |

---

## Assembly Instructions

### Step 1: Frame Assembly

**Time: 30 minutes**

1. **Assemble X650 frame**
   - Attach 4 arms to center plate
   - Use provided screws (M3x8)
   - Ensure arms are symmetric

2. **Mount landing gear**
   - Attach 4 landing legs
   - Height: ~15cm clearance

3. **Install power distribution board (PDB)**
   - Center of frame
   - Solder battery connector (XT60)

### Step 2: Motor and ESC Installation

**Time: 1 hour**

1. **Mount motors to arms**
   - DJI 2212 motors
   - Check rotation direction:
     - Front-left: CCW
     - Front-right: CW
     - Rear-left: CW
     - Rear-right: CCW

2. **Connect ESCs**
   - Solder ESC to motor (3 wires)
   - Solder ESC to PDB (red/black)
   - Route signal wire to flight controller

3. **Install propellers**
   - Match rotation direction
   - CW props on CW motors
   - CCW props on CCW motors

### Step 3: Flight Controller (Pixhawk 4)

**Time: 45 minutes**

1. **Mount Pixhawk 4**
   - Center of frame (above PDB)
   - Use vibration dampeners
   - Arrow points forward

2. **Connect components:**
   ```
   GPS Module    → GPS 1 port
   Telemetry     → TELEM 1 port
   RC Receiver   → RC IN port
   ESC Signal 1  → MAIN OUT 1
   ESC Signal 2  → MAIN OUT 2
   ESC Signal 3  → MAIN OUT 3
   ESC Signal 4  → MAIN OUT 4
   Power Module  → POWER 1 port
   ```

3. **External compass**
   - Mount GPS+compass on mast
   - 10cm+ above electronics
   - Arrow points forward
   - Connect I2C cable

### Step 4: Raspberry Pi 5 Setup

**Time: 1 hour**

1. **Install Hailo AI HAT+ on Pi 5**
   - Align 40-pin GPIO header
   - Press firmly to connect
   - Secure with standoffs

2. **Mount Pi 5 on frame**
   - Top plate or side mount
   - Good ventilation required
   - Secure with M2.5 screws

3. **Connect Camera Module v3**
   - Insert ribbon cable into Pi 5
   - CSI/DSI port (near USB-C)
   - Lift tab, insert cable (contacts down), close tab
   - Mount camera facing down

4. **Connect Pi to Pixhawk**
   - USB cable: Pi USB → Pixhawk USB
   - This provides MAVLink serial connection

5. **Power Pi 5**
   - Use 5V 5A BEC from PDB
   - Or separate battery (recommended for testing)
   - USB-C power input

### Step 5: Wiring Diagram

```
                    ┌─────────────┐
                    │   Battery   │
                    │  6S 5000mAh │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │Power Module │
                    │    PM07     │
                    └──┬────────┬─┘
                       │        │
             ┌─────────▼─┐   ┌─▼────────────┐
             │ Pixhawk 4 │   │     PDB      │
             │           │   │              │
             └─┬─┬─┬─┬─┬─┘   └─┬─┬─┬─┬─┬──┘
               │ │ │ │ │       │ │ │ │ │
               │ │ │ │ └───────┼─┼─┼─┼─┼─ RC Receiver
               │ │ │ └─────────┼─┼─┼─┼─┼─ Telemetry Radio
               │ │ └───────────┼─┼─┼─┼─┼─ GPS+Compass
               │ └─────────────┼─┼─┼─┼─┼─ USB to Pi 5
               └───────────────┼─┼─┼─┼─┘
                               │ │ │ │
                            ┌──▼─▼─▼─▼──┐
                            │ ESC 1-4   │
                            └──┬─┬─┬─┬──┘
                               │ │ │ │
                            ┌──▼─▼─▼─▼──┐
                            │Motors 1-4 │
                            └───────────┘

         ┌──────────────────────────┐
         │    Raspberry Pi 5        │
         │  + Hailo AI HAT+         │
         │  + Camera Module v3      │
         └────────┬─────────────────┘
                  │ USB
                  ▼
            To Pixhawk 4
```

---

## Software Configuration

### Step 1: Pixhawk Firmware

1. **Install QGroundControl** on laptop
   - Download from http://qgroundcontrol.com
   - Connect Pixhawk via USB

2. **Flash PX4 firmware**
   - Vehicle Setup → Firmware
   - Select PX4 Flight Stack
   - Choose "Standard Version (stable)"
   - Wait for flash to complete

3. **Configure airframe**
   - Vehicle Setup → Airframe
   - Select "Quadrotor X"
   - Apply and restart

4. **Calibrate sensors**
   - Accelerometer calibration
   - Compass calibration (rotate in all axes)
   - Radio calibration (bind RC transmitter)
   - Flight modes (set MANUAL, STABILIZE, AUTO)

5. **Configure parameters**
   ```
   # MAVLink serial port (for Pi connection)
   MAV_1_CONFIG = TELEM 2
   MAV_1_MODE = Normal
   SER_TEL2_BAUD = 57600

   # Safety settings
   COM_RC_LOSS_T = 1.0  # RC loss timeout (seconds)
   COM_LOW_BAT_ACT = 2  # Return mode on low battery

   # Geofence (set limits)
   GF_ACTION = 1  # RTL on breach
   GF_MAX_HOR_DIST = 500  # meters
   GF_MAX_VER_DIST = 120  # meters
   ```

### Step 2: Raspberry Pi OS

1. **Flash OS to MicroSD**
   - Use Raspberry Pi Imager
   - Choose "Raspberry Pi OS (64-bit)"
   - Configure WiFi and SSH in advanced settings

2. **Boot Pi and SSH**
   ```bash
   ssh pi@raspberrypi.local
   # Default password: raspberry
   ```

3. **Update system**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo reboot
   ```

4. **Configure interfaces**
   ```bash
   sudo raspi-config
   ```
   - Interface Options → Camera → Enable
   - Interface Options → I2C → Enable
   - Advanced → Expand Filesystem

5. **Install Hailo drivers**
   ```bash
   # Download from https://hailo.ai/developer-zone/
   wget https://hailo.ai/downloads/hailort-4.17.0-linux-aarch64.deb
   sudo dpkg -i hailort-4.17.0-linux-aarch64.deb

   # Verify
   hailortcli fw-control identify
   # Should show: Hailo-8L AI Processor
   ```

---

## Performance Testing

### Camera Test

```bash
# Test camera capture
libcamera-hello -t 5000

# Take still image
libcamera-still -o test.jpg

# Record video
libcamera-vid -o test.h264 -t 10000
```

### Hailo Inference Test

```bash
# Download test model
cd ~/flying-gem-brain/models
wget https://hailo-model-zoo.s3.amazonaws.com/ModelZoo/Compiled/v2.11.0/hailo8l/yolov8n.hef

# Run benchmark
hailortcli benchmark yolov8n.hef
# Should show ~30 FPS at 640x640
```

### MAVLink Test

```bash
# Install MAVProxy
pip install MAVProxy

# Connect to Pixhawk
mavproxy.py --master=/dev/ttyACM0 --baudrate=57600

# Should see heartbeat messages
# Try command: mode GUIDED
```

### Full System Test

```bash
cd ~/flying-gem-brain
python edge/edge_node.py --drone-id=test-drone --nats-url=nats://localhost:4222

# Should see:
# - NATS connection established
# - Telemetry publishing at 1 Hz
# - Camera feed active
# - MAVLink heartbeat
```

---

## Pre-Flight Checklist

### Hardware

- [ ] All screws tight
- [ ] Props secure (correct rotation)
- [ ] Battery charged and connected
- [ ] Pi 5 powered and booted
- [ ] Camera lens clean
- [ ] GPS has 3D fix (10+ satellites)
- [ ] RC transmitter on and bound
- [ ] Telemetry link active

### Software

- [ ] Pixhawk armed successfully
- [ ] RC failsafe configured
- [ ] Geofence enabled
- [ ] Edge node running
- [ ] NATS mesh connected
- [ ] Detections publishing
- [ ] Ground control receiving telemetry

### Safety

- [ ] Flight area clear
- [ ] No-fly zones checked
- [ ] Emergency landing spot identified
- [ ] RC override tested
- [ ] Return-to-launch altitude set
- [ ] Operator ratio: 1:X (X ≤ 10)

---

## Troubleshooting

### Pi Won't Boot

**Symptom:** No HDMI output, no SSH connection

**Solutions:**
1. Check power supply (5V 5A required)
2. Re-flash SD card
3. Remove Hailo HAT, test Pi alone
4. Try different SD card

### Hailo Not Detected

**Symptom:** `hailortcli` shows "No devices found"

**Solutions:**
```bash
# Check USB enumeration
lsusb | grep Hailo

# Check kernel logs
dmesg | grep hailo

# Reinstall driver
sudo dpkg --purge hailort
sudo dpkg -i hailort-4.17.0-linux-aarch64.deb
```

### Camera Not Working

**Symptom:** `libcamera-hello` fails

**Solutions:**
```bash
# Check cable connection
vcgencmd get_camera
# Should show: supported=1 detected=1

# Enable legacy camera
sudo raspi-config
# Interface Options → Legacy Camera → Enable

# Reboot
sudo reboot
```

### Pixhawk Not Arming

**Symptom:** Arm button rejected

**Possible Causes:**
- RC not calibrated
- Accelerometer not calibrated
- Compass error
- GPS no fix
- Battery voltage low
- Safety switch not pressed

**Check:**
```bash
# Connect via MAVProxy
mavproxy.py --master=/dev/ttyACM0 --baudrate=57600

# Check pre-arm status
arm check
```

### Low Detection FPS

**Symptom:** YOLOv8n running <10 FPS

**Solutions:**
1. Check Hailo temperature: `hailortcli sensor`
2. Verify 640x640 input (not larger)
3. Disable HDMI output (saves power)
4. Use performance governor:
   ```bash
   sudo cpufreq-set -g performance
   ```

---

## Maintenance

### Weekly

- Clean camera lens
- Check prop condition (cracks, chips)
- Tighten all screws
- Test battery voltage (no sag)
- Update flight logs

### Monthly

- Update Raspberry Pi OS
- Clean motor bearings
- Check ESC temperatures
- Calibrate compass
- Backup SD card

### After Every Flight

- Check for damage
- Download telemetry logs
- Review detection accuracy
- Note any anomalies

---

## Advanced Configurations

### Dual Camera Setup

For stereo vision or wider coverage:

```python
# Add second camera
# Connect to second CSI port on Pi 5
# Modify edge_node.py to handle dual streams
```

### RTK GPS (Centimeter Accuracy)

For precision landing:

```
Hardware: Ublox ZED-F9P
Cost: +$200
Accuracy: 2cm horizontal

Connect to Pixhawk GPS 2 port
Configure PX4 for RTK
```

### LTE Modem (Extended Range)

For beyond-visual-line-of-sight (BVLOS):

```bash
# Add LTE HAT to Pi
# Examples: Sixfab LTE HAT, Waveshare SIM7600

# Configure as backup to 915MHz radio
# NATS over LTE when out of radio range
```

### Thermal Camera (Night Ops)

For low-light detection:

```
Hardware: FLIR Lepton 3.5
Cost: +$200
Integration: Via SPI on Pi 5

Modify hailo_detector.py for thermal input
```

---

## Cost Optimization

### Budget Build (~$700)

- Use Raspberry Pi 4 (8GB): -$20
- Use Raspberry Pi AI HAT (13 TOPS): -$25
- Use cheaper frame (F450): -$100
- Use 4S battery instead of 6S: -$30
- Total: **~$700**

Performance impact: ~20 FPS instead of 30 FPS

### Premium Build (~$1,500)

- Use NVIDIA Jetson Orin Nano (40 TOPS): +$400
- Use high-end carbon fiber frame: +$200
- Use RTK GPS: +$200
- Use LTE modem: +$100
- Total: **~$1,500**

Performance gain: 60+ FPS, cm-accuracy GPS, BVLOS capability

---

## Next Steps

1. ✅ Complete hardware assembly
2. ✅ Configure Pixhawk firmware
3. ✅ Setup Raspberry Pi + Hailo
4. ✅ Run performance tests
5. → **Test edge node code** ([edge/README.md](../edge/README.md))
6. → **Run swarm simulation** ([simulation/README.md](../simulation/README.md))
7. → **Deploy to real hardware**

---

**Safety First:** Always follow local aviation regulations and maintain visual line of sight during testing.

**For assembly videos and detailed guides, visit:** [infinity-folder.no](https://infinity-folder.no)
