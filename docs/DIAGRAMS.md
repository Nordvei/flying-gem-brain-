# Architecture Diagrams

Visual representation of Flying GEM Brain system architecture.

---

## 1. Three-Tier GEM Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GLOBAL TIER                              │
│                    (Ground Control Station)                     │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │     SAGE     │  │  PostgreSQL  │  │  Prometheus  │         │
│  │ Coordinator  │◄─┤   Pattern    │◄─┤   Metrics    │         │
│  │              │  │   Database   │  │ Aggregation  │         │
│  └──────┬───────┘  └──────────────┘  └──────────────┘         │
│         │                                                       │
│         │           ┌──────────────┐                           │
│         └──────────►│   Grafana    │                           │
│                     │  Dashboard   │                           │
│                     └──────────────┘                           │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ NATS Messaging (<500ms)
                              │ Pattern Federation
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                         MESH TIER                               │
│                   (Swarm Coordination)                          │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              NATS Event Mesh                           │   │
│  │  • Pub/Sub Communication                               │   │
│  │  • Pattern Sharing                                     │   │
│  │  • Consensus Protocol                                  │   │
│  │  • Self-Healing Failover                               │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────┬───────────────────────┬───────────────────────┘
                  │                       │
┌─────────────────▼───────┐   ┌──────────▼───────────┐
│      EDGE TIER          │   │      EDGE TIER       │   (Repeat for
│   (Drone 1 Brain)       │   │   (Drone 2 Brain)    │    5-10 drones)
│                         │   │                      │
│  ┌──────────────────┐   │   │  ┌─────────────────┐│
│  │ Raspberry Pi 5   │   │   │  │ Raspberry Pi 5  ││
│  │ + Hailo AI HAT+  │   │   │  │ + Hailo AI HAT+ ││
│  │   (26 TOPS)      │   │   │  │   (26 TOPS)     ││
│  └────────┬─────────┘   │   │  └───────┬─────────┘│
│           │             │   │          │          │
│  ┌────────▼─────────┐   │   │  ┌───────▼────────┐ │
│  │ YOLOv8n Detection│   │   │  │ YOLOv8n Detection│
│  │   (30 FPS)       │   │   │  │   (30 FPS)      │ │
│  └────────┬─────────┘   │   │  └───────┬────────┘ │
│           │             │   │          │          │
│  ┌────────▼─────────┐   │   │  ┌───────▼────────┐ │
│  │   Pixhawk 4      │   │   │  │   Pixhawk 4    │ │
│  │ Flight Controller│   │   │  │ Flight Controller│
│  └──────────────────┘   │   │  └────────────────┘ │
└─────────────────────────┘   └────────────────────┘
```

---

## 2. Edge Node Architecture

```
┌─────────────────────────────────────────────────────────┐
│              EDGE NODE (Per Drone)                      │
│                                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │         Raspberry Pi 5 (Quad-Core ARM)         │   │
│  │                                                 │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │      Hailo AI HAT+ (26 TOPS NPU)         │  │   │
│  │  │                                           │  │   │
│  │  │  ┌─────────────────────────────────────┐ │  │   │
│  │  │  │   YOLOv8n Inference Engine          │ │  │   │
│  │  │  │   • 640x640 input                   │ │  │   │
│  │  │  │   • 30 FPS throughput                │ │  │   │
│  │  │  │   • 80 COCO classes                  │ │  │   │
│  │  │  └───────────┬─────────────────────────┘ │  │   │
│  │  └──────────────┼───────────────────────────┘  │   │
│  └─────────────────┼──────────────────────────────┘   │
│                    │                                   │
│  ┌─────────────────▼─────────────────────────────┐   │
│  │         Edge Node Orchestrator                 │   │
│  │                                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │NATS Client   │  │MAVLink Bridge│           │   │
│  │  │• Pub/Sub     │  │• Telemetry   │           │   │
│  │  │• Commands    │  │• Commands    │           │   │
│  │  │• Patterns    │  │• Failsafe    │           │   │
│  │  └──────┬───────┘  └──────┬───────┘           │   │
│  └─────────┼──────────────────┼───────────────────┘   │
│            │                  │                       │
└────────────┼──────────────────┼───────────────────────┘
             │                  │
             │                  │
        ┌────▼────┐        ┌────▼────────┐
        │  NATS   │        │  Pixhawk 4  │
        │  Mesh   │        │   Flight    │
        │         │        │ Controller  │
        └─────────┘        └─────────────┘
```

---

## 3. Communication Flow

```
Edge Node 1                NATS Mesh               Global Control
┌──────────┐              ┌──────────┐              ┌──────────┐
│          │              │          │              │          │
│ Detect:  │              │          │              │  SAGE    │
│ Vehicle  │──publish────►│ gem.     │──forward────►│ receives │
│ 0.87 conf│              │ detection│              │ pattern  │
│          │              │          │              │          │
└──────────┘              └──────────┘              └──┬───────┘
                                                       │
Edge Node 2                                            │
┌──────────┐                                           │
│          │                                           │
│ Receives │◄──────subscribe to pattern───────────────┘
│ shared   │              ┌──────────┐
│ pattern  │◄─────────────┤ gem.     │
│          │              │ pattern. │
└──────────┘              │ vehicle  │
                          └──────────┘

Timeline:
─────────────────────────────────────────────────────►
  0ms        50ms       100ms      150ms      200ms

  Detect  →  Publish →  SAGE   →  Share  →  Other
             to NATS    Process   Pattern   Drones
                                            Receive

  Total latency: <200ms for full swarm awareness
```

---

## 4. Swarm Coordination Behaviors

```
SEPARATION (Avoid Collision)
────────────────────────────

  Drone A          Drone B
     ●                ●
      ╲              ╱
       ╲            ╱
        ╲          ╱
         ╲  <100m ╱
          ╲      ╱
           ╲    ╱
            ╲  ╱
             ×  ← Too close!
            ╱  ╲
           ╱    ╲
          ●      ● ← Move apart
       Drone A  Drone B


COHESION (Stay Together)
────────────────────────

        Swarm Center
            ●
           ╱│╲
          ╱ │ ╲
         ╱  │  ╲
    ●───────┼───────●
   D1       │       D3
            │
            ●
           D2

   If D1 drifts >200m → Move toward center


ALIGNMENT (Match Velocity)
──────────────────────────

   D1 →→→     D2 →
   D3 →→      D4 →→

   Average velocity: →→
   All adjust to: →→

   D1 →→     D2 →→
   D3 →→     D4 →→


TARGET SEEKING
──────────────

              ★ Target detected
             ╱│╲
            ╱ │ ╲
           ╱  │  ╲
          ●───●───●
         D1  D2  D3

   All drones converge on shared target
```

---

## 5. Operator to Drone Ratio

```
TRADITIONAL (1:1)
─────────────────

  Operator 1 ───── Drone 1
  Operator 2 ───── Drone 2
  Operator 3 ───── Drone 3
  Operator 4 ───── Drone 4
  Operator 5 ───── Drone 5

  Operators needed: 5
  Cost: 5x operator salaries
  Scalability: Linear


FLYING GEM BRAIN (1:10+)
────────────────────────

                          Drone 1 (Autonomous)
                         ╱
                        ╱  Drone 2 (Autonomous)
                       ╱  ╱
  Operator 1 ─────────●──── Drone 3 (Autonomous)
         │             ╲
         │              ╲  Drone 4 (Autonomous)
    High-level          ╲
     Commands            Drone 5 (Autonomous)
     Only                 │
                         ... (Scale to 10+)

  Operators needed: 1
  Cost: 1x operator salary
  Scalability: Exponential

  FORCE MULTIPLIER: 10x
```

---

## 6. Data Flow Pipeline

```
┌─────────────┐
│   Camera    │
│  12MP 30FPS │
└──────┬──────┘
       │ Raw Frame
       ▼
┌─────────────┐
│ Preprocessing│
│  640x640    │
│  Normalize  │
└──────┬──────┘
       │ Prepared Frame
       ▼
┌─────────────┐
│  Hailo AI   │
│  YOLOv8n    │
│  Inference  │
└──────┬──────┘
       │ Raw Detections
       ▼
┌─────────────┐
│    NMS      │
│  Filtering  │
└──────┬──────┘
       │ Filtered Detections
       ▼
┌─────────────┐
│  NATS Pub   │
│  gem.detect │
└──────┬──────┘
       │
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│    SAGE     │    │Other Drones │
│  Coordinator│    │  Subscribe  │
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────┐
│ PostgreSQL  │
│   Pattern   │
│  Database   │
└─────────────┘

Total Latency: ~50ms (camera to NATS)
```

---

## 7. Failure Recovery

```
SCENARIO: Drone 3 Fails

BEFORE FAILURE:
───────────────
      ●─────●
     D1     D2
      │  ×  │
      │ D3  │
      │     │
      ●─────●
     D4     D5

  5 drones in formation


DURING FAILURE:
───────────────
      ●─────●
     D1     D2
      │  ⚠  │  ← D3 loses battery
      │ D3  │     Sends "emergency" status
      │     │
      ●─────●
     D4     D5


AFTER SELF-HEALING:
───────────────────
      ●───●
     D1   D2
      │   │
      │   │  ← D3 removed from swarm
      │   │
      ●───●
     D4   D5

  4 drones continue mission
  Operator notified of reduction
  No mission failure


RECOVERY TIME: <5 seconds
```

---

## 8. Hardware Stack

```
┌──────────────────────────────────────────┐
│          Physical Drone                  │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │      Raspberry Pi 5 Stack          │ │
│  │                                    │ │
│  │  ┌──────────────────────────────┐ │ │
│  │  │   Hailo AI HAT+              │ │ │  ← AI Accelerator
│  │  │   26 TOPS NPU                │ │ │
│  │  └──────────────────────────────┘ │ │
│  │                                    │ │
│  │  ┌──────────────────────────────┐ │ │
│  │  │   Raspberry Pi 5             │ │ │  ← Main Compute
│  │  │   Quad-core ARM              │ │ │
│  │  │   8GB RAM                    │ │ │
│  │  └──────────────────────────────┘ │ │
│  └────────────┬───────────────────────┘ │
│               │ USB                     │
│  ┌────────────▼───────────────────────┐ │
│  │      Pixhawk 4                     │ │  ← Flight Control
│  │      Flight Controller             │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌──────────┐  ┌──────────┐             │
│  │  GPS     │  │ Camera   │             │  ← Sensors
│  │  Module  │  │ Module   │             │
│  └──────────┘  └──────────┘             │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │   Motors + ESCs + Frame          │   │  ← Propulsion
│  └──────────────────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │   6S LiPo Battery                │   │  ← Power
│  └──────────────────────────────────┘   │
└──────────────────────────────────────────┘

Total Cost: ~$1,000
Total Weight: ~2.5kg
Flight Time: ~20-30 minutes
```

---

**These diagrams are referenced in the main [ARCHITECTURE.md](ARCHITECTURE.md) documentation.**
