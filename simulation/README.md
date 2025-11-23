# Swarm Simulation

Visual demonstration of Flying GEM Brain swarm coordination principles.

## Features

- **5-Drone Swarm** - Demonstrates 1:5 operator ratio
- **Autonomous Coordination** - Separation, cohesion, alignment behaviors
- **Self-Healing** - Press SPACE to fail a drone, watch swarm adapt
- **Target Detection** - Collective intelligence to find and track targets
- **NATS Mesh Visualization** - See communication links between drones
- **Real-Time Metrics** - Active drones, detections, mesh messages

## Requirements

```bash
pip install pygame
```

## Run Simulation

```bash
python simulation/swarm_sim.py
```

## Controls

- **SPACE** - Simulate drone failure (test self-healing)
- **R** - Reset simulation
- **ESC** - Exit

## What This Demonstrates

### 1. Autonomous Coordination
Each drone makes independent decisions based on:
- **Separation** - Avoid crowding neighbors
- **Cohesion** - Stay close to swarm center
- **Alignment** - Match velocity with neighbors

### 2. Collective Intelligence
- Drones share target detections via mesh
- Swarm converges on detected targets
- Coordinated search patterns emerge

### 3. Self-Healing
- Remove drones (SPACE key)
- Swarm reorganizes automatically
- Mission continues with reduced capacity

### 4. Mesh Communication
- Blue lines show NATS mesh connections
- Line opacity indicates signal strength
- Communication range: 300 pixels

## Swarm Behaviors

### Separation (Avoid Collision)
```python
if distance < SEPARATION_DIST:
    move_away_from_neighbor()
```

### Cohesion (Stay Together)
```python
if distance < COHESION_DIST:
    move_toward_swarm_center()
```

### Alignment (Coordinate Movement)
```python
if distance < COHESION_DIST:
    match_neighbor_velocity()
```

### Target Seeking
```python
if target_detected_by_any_drone:
    all_drones_converge_on_target()
```

## Visual Elements

| Element | Color | Meaning |
|---------|-------|---------|
| Green circles | Active drones | Operational |
| Gray circles | Inactive drones | Failed/low battery |
| Blue lines | NATS mesh | Communication links |
| Gold circles | Targets | Objects to detect |
| Red rings | Detection radius | Sensor range |
| Battery bars | Green → Red | Remaining power |

## Simulation Parameters

```python
DRONE_SPEED = 2.0          # Max speed (pixels/frame)
SEPARATION_DIST = 100      # Min distance between drones
COHESION_DIST = 200        # Swarm cohesion radius
DETECTION_RANGE = 150      # Target detection radius
COMMUNICATION_RANGE = 300  # NATS mesh range
```

## Real-World Mapping

| Simulation | Real Drone |
|------------|------------|
| 1 pixel | ~1 meter |
| DETECTION_RANGE (150px) | 150m sensor range |
| COMMUNICATION_RANGE (300px) | 300m radio range |
| Battery drain | ~30min flight time |

## Future Enhancements

- [ ] Add obstacles (terrain, no-fly zones)
- [ ] Multi-target tracking
- [ ] Formation flying modes
- [ ] Wind simulation
- [ ] 3D visualization
- [ ] Real drone telemetry replay

## Educational Use

This simulation is perfect for:
- **Demonstrations** - Show swarm intelligence concepts
- **Testing** - Validate coordination algorithms
- **Training** - Operator familiarization
- **Development** - Prototype new behaviors

---

**This simulation demonstrates the core principles that Flying GEM Brain uses for real drone coordination.**
