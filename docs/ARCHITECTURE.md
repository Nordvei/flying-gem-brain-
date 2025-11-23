# Flying GEM Brain - Architecture

## Overview

Flying GEM Brain uses a **three-tier architecture** (Global-Edge-Mesh) adapted from the production-proven IFP Platform.

## Three Tiers

### 1. GLOBAL TIER (Ground Control Station)

**Components:**
- **SAGE Coordinator** - Main orchestrator
- **PostgreSQL** - Pattern database
- **Prometheus** - Metrics aggregation
- **Grafana** - Operator dashboards

**Responsibilities:**
- Mission planning
- Pattern aggregation from all drones
- Strategic decision-making
- Operator interface

**Hardware:**
- Server/workstation (ARM or x86)
- 4GB+ RAM
- Network connectivity

---

### 2. EDGE TIER (Individual Drones)

**Components:**
- **Raspberry Pi 5** - Main compute (quad-core ARM, 8GB RAM)
- **Hailo AI HAT+** - 26 TOPS NPU for YOLOv8n inference
- **Camera Module** - Raspberry Pi Camera v3 (12MP)
- **Pixhawk 4** - Flight controller with MAVLink

**Responsibilities:**
- Real-time object detection (YOLOv8n @ 30 FPS)
- Local decision-making
- Telemetry processing
- Emergency autonomy

**Key Features:**
- Runs independently if mesh connection lost
- Low power consumption (~15W total)
- Local pattern detection
- Fallback behaviors

---

### 3. MESH TIER (Swarm Coordination)

**Components:**
- **NATS Messaging** - Pub/sub communication
- **PostgreSQL Replication** - Pattern sharing
- **Consensus Protocol** - Coordinated actions

**Responsibilities:**
- Inter-drone communication (<500ms latency)
- Collective intelligence
- Task distribution
- Self-healing coordination

**Key Features:**
- No single point of failure
- Automatic failover
- Pattern federation
- Distributed consensus

---

## Data Flow

```
┌─────────────────────────────────────────────────┐
│            GLOBAL TIER                          │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐    │
│  │  SAGE   │  │PostgreSQL│  │  Grafana   │    │
│  │Coordinator│◄┤  Patterns│◄┤ Dashboards │    │
│  └────▲────┘  └─────▲────┘  └────────────┘    │
│       │             │                           │
└───────┼─────────────┼───────────────────────────┘
        │             │
        │   NATS Mesh │ (Pub/Sub)
        │             │
┌───────▼─────────────▼───────────────────────────┐
│            MESH TIER                            │
│  Drone 1 ◄───► Drone 2 ◄───► Drone 3 ◄───► ... │
└─────────────────────────────────────────────────┘
        │             │             │
┌───────▼───┐   ┌─────▼────┐  ┌────▼─────┐
│ EDGE TIER │   │EDGE TIER │  │EDGE TIER │
│  Pi 5 +   │   │ Pi 5 +   │  │ Pi 5 +   │
│  Hailo    │   │ Hailo    │  │ Hailo    │
│  Camera   │   │ Camera   │  │ Camera   │
│  Pixhawk  │   │ Pixhawk  │  │ Pixhawk  │
└───────────┘   └──────────┘  └──────────┘
```

---

## Communication Protocols

### NATS Messaging Topics

```
gem.telemetry.{drone_id}      - Drone status updates (1 Hz)
gem.detection.{drone_id}      - Object detections (real-time)
gem.command.{drone_id}        - Commands to specific drone
gem.command.broadcast         - Commands to all drones
gem.pattern.{pattern_id}      - Pattern sharing
gem.consensus.{proposal_id}   - Consensus voting
```

### MAVLink (Drone ↔ Pixhawk)

- **Telemetry:** Position, velocity, battery, status
- **Commands:** Waypoints, RTL, loiter, land
- **Heartbeat:** Connection monitoring (1 Hz)

---

## Pattern Federation

Drones share detected patterns via PostgreSQL:

```sql
CREATE TABLE patterns (
    pattern_id UUID PRIMARY KEY,
    drone_id VARCHAR(50),
    pattern_type VARCHAR(50),
    confidence FLOAT,
    location POINT,
    timestamp TIMESTAMP,
    metadata JSONB
);
```

**Pattern Types:**
- `object_detection` - Detected objects (vehicle, person, etc.)
- `anomaly` - Unusual behavior
- `coordination` - Multi-drone patterns
- `tactical` - Mission-specific patterns

---

## Self-Healing

### Failure Scenarios

**1. Drone Failure**
- Other drones redistribute tasks
- Mission continues with reduced capacity
- Global tier updates mission plan

**2. Mesh Connection Loss**
- Drone operates autonomously
- Follows last known mission plan
- Attempts reconnection every 5 seconds

**3. Global Tier Failure**
- Drones continue current mission
- SAGE coordinator role can migrate
- Manual override always available

---

## Consensus Protocol

For coordinated actions (formation changes, target prioritization):

1. **Proposal:** Initiating drone broadcasts proposal
2. **Voting:** Each drone votes based on local state
3. **Threshold:** Action requires 51%+ agreement
4. **Execution:** All drones execute simultaneously
5. **Timeout:** 2-second timeout, fallback to default

---

## Security

- **No internet required** - All communication local mesh
- **Encrypted mesh** - NATS TLS encryption
- **Authentication** - Token-based drone identity
- **Command validation** - All commands signed
- **Emergency stop** - Hardware kill switch on operator console

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Mesh Latency | <500ms | TBD |
| Detection Rate | 30 FPS | TBD |
| Failover Time | <5s | TBD |
| Battery Life | 30 min | TBD |
| Swarm Size | 10+ drones | TBD |

---

## Future Enhancements

- **GPU Acceleration** - Nvidia DGX Spark for global tier
- **Advanced ML** - Pattern prediction, trajectory planning
- **Multi-Modal Sensors** - Thermal, LiDAR, radar
- **Larger Swarms** - 50+ drone coordination
- **Edge Training** - On-device model fine-tuning
