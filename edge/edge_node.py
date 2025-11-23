#!/usr/bin/env python3
"""
Flying GEM Brain - Edge Node
Runs on each drone (Raspberry Pi 5 + Hailo AI)
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from typing import Optional, List
import argparse

# Note: These imports would be available on actual hardware
# For development, install: pip install pynats psycopg2-binary
try:
    from pynats import NATSClient
except ImportError:
    print("Warning: pynats not installed. Install with: pip install pynats")
    NATSClient = None

try:
    import psycopg2
except ImportError:
    print("Warning: psycopg2 not installed. Install with: pip install psycopg2-binary")
    psycopg2 = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DRONE-%(name)s - %(levelname)s - %(message)s'
)


@dataclass
class Telemetry:
    """Drone telemetry data"""
    drone_id: str
    timestamp: float
    latitude: float
    longitude: float
    altitude: float
    battery: float
    status: str  # "active", "returning", "emergency"


@dataclass
class Detection:
    """Object detection result"""
    drone_id: str
    timestamp: float
    object_class: str  # "vehicle", "person", etc.
    confidence: float
    bbox: List[float]  # [x, y, width, height]
    latitude: float
    longitude: float


class EdgeNode:
    """Main edge node class running on each drone"""

    def __init__(self, drone_id: str, nats_url: str = "nats://localhost:4222"):
        self.drone_id = drone_id
        self.nats_url = nats_url
        self.nats_client = None
        self.running = False

        # Drone state
        self.battery = 100.0
        self.position = (0.0, 0.0, 0.0)  # lat, lon, alt
        self.status = "active"

        # Performance metrics
        self.detections_count = 0
        self.messages_sent = 0
        self.uptime_start = time.time()

        self.logger = logging.getLogger(drone_id)

    async def connect_nats(self):
        """Connect to NATS mesh"""
        if NATSClient is None:
            self.logger.warning("NATS not available - running in simulation mode")
            return

        try:
            self.nats_client = NATSClient(url=self.nats_url)
            await self.nats_client.connect()
            self.logger.info(f"Connected to NATS at {self.nats_url}")

            # Subscribe to relevant topics
            await self.nats_client.subscribe(
                f"gem.command.{self.drone_id}",
                callback=self.handle_command
            )
            await self.nats_client.subscribe(
                "gem.command.broadcast",
                callback=self.handle_broadcast
            )

            self.logger.info("Subscribed to command topics")
        except Exception as e:
            self.logger.error(f"Failed to connect to NATS: {e}")

    async def publish_telemetry(self):
        """Publish telemetry to NATS mesh"""
        telemetry = Telemetry(
            drone_id=self.drone_id,
            timestamp=time.time(),
            latitude=self.position[0],
            longitude=self.position[1],
            altitude=self.position[2],
            battery=self.battery,
            status=self.status
        )

        topic = f"gem.telemetry.{self.drone_id}"
        message = json.dumps(asdict(telemetry))

        if self.nats_client:
            try:
                await self.nats_client.publish(topic, message.encode())
                self.messages_sent += 1
            except Exception as e:
                self.logger.error(f"Failed to publish telemetry: {e}")
        else:
            self.logger.debug(f"Telemetry (simulated): {message}")

    async def publish_detection(self, detection: Detection):
        """Publish object detection to NATS mesh"""
        topic = f"gem.detection.{self.drone_id}"
        message = json.dumps(asdict(detection))

        if self.nats_client:
            try:
                await self.nats_client.publish(topic, message.encode())
                self.messages_sent += 1
                self.detections_count += 1
                self.logger.info(f"Detection published: {detection.object_class} ({detection.confidence:.2f})")
            except Exception as e:
                self.logger.error(f"Failed to publish detection: {e}")
        else:
            self.logger.info(f"Detection (simulated): {detection.object_class}")

    async def handle_command(self, message):
        """Handle commands sent to this specific drone"""
        try:
            cmd = json.loads(message.data.decode())
            self.logger.info(f"Received command: {cmd}")

            cmd_type = cmd.get("type")

            if cmd_type == "rtl":
                self.logger.info("Executing Return To Launch")
                self.status = "returning"

            elif cmd_type == "loiter":
                self.logger.info("Executing Loiter command")
                self.status = "loitering"

            elif cmd_type == "waypoint":
                waypoint = cmd.get("waypoint")
                self.logger.info(f"Navigating to waypoint: {waypoint}")

            elif cmd_type == "emergency_land":
                self.logger.warning("Emergency land initiated!")
                self.status = "emergency"

        except Exception as e:
            self.logger.error(f"Error handling command: {e}")

    async def handle_broadcast(self, message):
        """Handle broadcast commands to all drones"""
        try:
            cmd = json.loads(message.data.decode())
            self.logger.info(f"Received broadcast: {cmd}")

            # Handle broadcast commands
            if cmd.get("type") == "formation_change":
                formation = cmd.get("formation")
                self.logger.info(f"Changing to formation: {formation}")

        except Exception as e:
            self.logger.error(f"Error handling broadcast: {e}")

    async def run_detection(self):
        """Simulated object detection (would use Hailo AI on real hardware)"""
        # In real implementation, this would:
        # 1. Capture frame from Raspberry Pi Camera v3
        # 2. Run YOLOv8n inference on Hailo AI HAT+
        # 3. Process detections
        # 4. Publish to NATS mesh

        # Simulated detection for demonstration
        if self.status == "active":
            # Simulate occasional detection
            import random
            if random.random() < 0.1:  # 10% chance per cycle
                detection = Detection(
                    drone_id=self.drone_id,
                    timestamp=time.time(),
                    object_class=random.choice(["vehicle", "person", "building"]),
                    confidence=random.uniform(0.7, 0.95),
                    bbox=[100, 100, 50, 50],
                    latitude=self.position[0],
                    longitude=self.position[1]
                )
                await self.publish_detection(detection)

    async def update_state(self):
        """Update drone state (battery, position, etc.)"""
        # Simulate battery drain
        self.battery = max(0, self.battery - 0.01)

        if self.battery < 20 and self.status == "active":
            self.logger.warning(f"Low battery: {self.battery:.1f}%")
            self.status = "returning"

        if self.battery == 0:
            self.logger.critical("Battery depleted!")
            self.status = "emergency"
            self.running = False

    async def main_loop(self):
        """Main edge node loop"""
        self.running = True
        self.logger.info(f"Edge node started for drone {self.drone_id}")

        # Connect to NATS
        await self.connect_nats()

        telemetry_interval = 1.0  # 1 Hz
        detection_interval = 0.1  # 10 Hz

        last_telemetry = time.time()
        last_detection = time.time()

        while self.running:
            try:
                current_time = time.time()

                # Publish telemetry at 1 Hz
                if current_time - last_telemetry >= telemetry_interval:
                    await self.publish_telemetry()
                    last_telemetry = current_time

                # Run detection at 10 Hz (simulates 30 FPS with batching)
                if current_time - last_detection >= detection_interval:
                    await self.run_detection()
                    last_detection = current_time

                # Update drone state
                await self.update_state()

                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.01)

            except KeyboardInterrupt:
                self.logger.info("Shutting down...")
                self.running = False
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(1)

        # Cleanup
        if self.nats_client:
            await self.nats_client.close()

        uptime = time.time() - self.uptime_start
        self.logger.info(f"Edge node stopped. Uptime: {uptime:.1f}s, "
                        f"Detections: {self.detections_count}, "
                        f"Messages: {self.messages_sent}")

    def run(self):
        """Run the edge node"""
        try:
            asyncio.run(self.main_loop())
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Flying GEM Brain - Edge Node")
    parser.add_argument("--drone-id", type=str, required=True,
                       help="Unique drone identifier (e.g., 'drone-1')")
    parser.add_argument("--nats-url", type=str, default="nats://localhost:4222",
                       help="NATS server URL")

    args = parser.parse_args()

    print("=" * 60)
    print("Flying GEM Brain - Edge Node")
    print("=" * 60)
    print(f"Drone ID: {args.drone_id}")
    print(f"NATS URL: {args.nats_url}")
    print("=" * 60)
    print()
    print("Press Ctrl+C to stop")
    print()

    node = EdgeNode(drone_id=args.drone_id, nats_url=args.nats_url)
    node.run()


if __name__ == "__main__":
    main()
