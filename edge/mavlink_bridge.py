#!/usr/bin/env python3
"""
Flying GEM Brain - MAVLink Bridge
Communication bridge between edge node and Pixhawk 4 flight controller
"""

import logging
import time
from typing import Optional, Callable
from dataclasses import dataclass

try:
    from pymavlink import mavutil
    MAVLINK_AVAILABLE = True
except ImportError:
    print("Warning: pymavlink not installed. Install with: pip install pymavlink")
    MAVLINK_AVAILABLE = False


@dataclass
class FlightTelemetry:
    """Flight controller telemetry"""
    latitude: float
    longitude: float
    altitude: float  # meters above sea level
    relative_altitude: float  # meters above home
    heading: int  # degrees
    groundspeed: float  # m/s
    airspeed: float  # m/s
    battery_voltage: float  # volts
    battery_current: float  # amps
    battery_remaining: int  # percent
    flight_mode: str
    armed: bool
    gps_fix: int  # 0=no GPS, 3=3D fix
    satellites_visible: int


class MAVLinkBridge:
    """
    Bridge for communicating with Pixhawk 4 flight controller

    Provides:
    - Telemetry streaming
    - Mission commands
    - Waypoint navigation
    - Emergency procedures
    """

    def __init__(
        self,
        connection_string: str = "/dev/ttyACM0",
        baud_rate: int = 57600
    ):
        """
        Initialize MAVLink bridge

        Args:
            connection_string: Serial port or UDP address
                Examples: "/dev/ttyACM0", "udp:127.0.0.1:14550"
            baud_rate: Serial baud rate (default 57600 for Pixhawk)
        """
        self.connection_string = connection_string
        self.baud_rate = baud_rate

        self.logger = logging.getLogger("MAVLinkBridge")

        self.master = None
        self.connected = False

        # Telemetry data
        self.last_heartbeat = 0
        self.last_gps = None
        self.last_attitude = None
        self.last_battery = None
        self.flight_mode = "UNKNOWN"
        self.armed = False

        if MAVLINK_AVAILABLE:
            self.connect()
        else:
            self.logger.warning("MAVLink not available - running in simulation mode")

    def connect(self):
        """Establish connection to flight controller"""
        try:
            self.logger.info(f"Connecting to flight controller: {self.connection_string}")

            self.master = mavutil.mavlink_connection(
                self.connection_string,
                baud=self.baud_rate
            )

            # Wait for heartbeat
            self.logger.info("Waiting for heartbeat...")
            self.master.wait_heartbeat(timeout=10)

            self.connected = True
            self.last_heartbeat = time.time()

            self.logger.info(f"Connected to system {self.master.target_system}, "
                           f"component {self.master.target_component}")

            # Request data streams
            self._request_data_streams()

        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            self.connected = False

    def _request_data_streams(self):
        """Request telemetry data streams at specific rates"""
        if not self.master:
            return

        # Request all streams at 4 Hz
        self.master.mav.request_data_stream_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_DATA_STREAM_ALL,
            4,  # Hz
            1   # Enable
        )

    def get_telemetry(self) -> Optional[FlightTelemetry]:
        """
        Get current flight telemetry

        Returns:
            FlightTelemetry object or None if not connected
        """
        if not self.connected:
            return self._simulate_telemetry()

        try:
            # Process incoming messages
            while True:
                msg = self.master.recv_match(blocking=False)
                if msg is None:
                    break

                msg_type = msg.get_type()

                if msg_type == "HEARTBEAT":
                    self.last_heartbeat = time.time()
                    self.flight_mode = mavutil.mode_string_v10(msg)
                    self.armed = msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED

                elif msg_type == "GLOBAL_POSITION_INT":
                    self.last_gps = msg

                elif msg_type == "ATTITUDE":
                    self.last_attitude = msg

                elif msg_type == "SYS_STATUS":
                    self.last_battery = msg

            # Build telemetry from latest data
            if self.last_gps and self.last_battery:
                return FlightTelemetry(
                    latitude=self.last_gps.lat / 1e7,
                    longitude=self.last_gps.lon / 1e7,
                    altitude=self.last_gps.alt / 1000.0,
                    relative_altitude=self.last_gps.relative_alt / 1000.0,
                    heading=self.last_gps.hdg / 100,
                    groundspeed=self.last_gps.vx / 100.0,
                    airspeed=self.last_gps.vy / 100.0,
                    battery_voltage=self.last_battery.voltage_battery / 1000.0,
                    battery_current=self.last_battery.current_battery / 100.0,
                    battery_remaining=self.last_battery.battery_remaining,
                    flight_mode=self.flight_mode,
                    armed=self.armed,
                    gps_fix=self.last_gps.fix_type if hasattr(self.last_gps, 'fix_type') else 3,
                    satellites_visible=self.last_gps.satellites_visible if hasattr(self.last_gps, 'satellites_visible') else 0
                )

            return None

        except Exception as e:
            self.logger.error(f"Error getting telemetry: {e}")
            return None

    def _simulate_telemetry(self) -> FlightTelemetry:
        """Simulate telemetry when not connected to real hardware"""
        import random

        return FlightTelemetry(
            latitude=59.9139 + random.uniform(-0.01, 0.01),  # Oslo area
            longitude=10.7522 + random.uniform(-0.01, 0.01),
            altitude=100.0 + random.uniform(-5, 5),
            relative_altitude=50.0 + random.uniform(-2, 2),
            heading=random.randint(0, 359),
            groundspeed=random.uniform(5, 15),
            airspeed=random.uniform(5, 15),
            battery_voltage=22.2 + random.uniform(-0.5, 0.5),
            battery_current=15.0 + random.uniform(-2, 2),
            battery_remaining=random.randint(60, 90),
            flight_mode="AUTO",
            armed=True,
            gps_fix=3,
            satellites_visible=12
        )

    def set_mode(self, mode: str) -> bool:
        """
        Set flight mode

        Args:
            mode: Flight mode string (e.g., "GUIDED", "RTL", "AUTO")

        Returns:
            True if successful
        """
        if not self.connected:
            self.logger.warning(f"Cannot set mode {mode} - not connected")
            return False

        try:
            # Get mode ID
            if mode not in self.master.mode_mapping():
                self.logger.error(f"Unknown mode: {mode}")
                return False

            mode_id = self.master.mode_mapping()[mode]

            # Send mode change command
            self.master.mav.set_mode_send(
                self.master.target_system,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                mode_id
            )

            self.logger.info(f"Set mode to {mode}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to set mode: {e}")
            return False

    def arm(self) -> bool:
        """Arm the vehicle"""
        if not self.connected:
            return False

        try:
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,  # confirmation
                1,  # arm
                0, 0, 0, 0, 0, 0
            )

            self.logger.info("Sent ARM command")
            return True

        except Exception as e:
            self.logger.error(f"Failed to arm: {e}")
            return False

    def disarm(self) -> bool:
        """Disarm the vehicle"""
        if not self.connected:
            return False

        try:
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,  # confirmation
                0,  # disarm
                0, 0, 0, 0, 0, 0
            )

            self.logger.info("Sent DISARM command")
            return True

        except Exception as e:
            self.logger.error(f"Failed to disarm: {e}")
            return False

    def goto_waypoint(self, lat: float, lon: float, alt: float) -> bool:
        """
        Navigate to GPS waypoint

        Args:
            lat: Latitude (decimal degrees)
            lon: Longitude (decimal degrees)
            alt: Altitude (meters above sea level)

        Returns:
            True if command sent successfully
        """
        if not self.connected:
            self.logger.warning("Cannot send waypoint - not connected")
            return False

        try:
            # Set mode to GUIDED
            self.set_mode("GUIDED")

            # Send waypoint command
            self.master.mav.mission_item_send(
                self.master.target_system,
                self.master.target_component,
                0,  # seq
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                2,  # current = 2 for guided mode
                1,  # autocontinue
                0, 0, 0, 0,  # params 1-4
                lat, lon, alt
            )

            self.logger.info(f"Sent waypoint: ({lat:.6f}, {lon:.6f}) @ {alt}m")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send waypoint: {e}")
            return False

    def return_to_launch(self) -> bool:
        """Execute Return To Launch (RTL)"""
        if not self.connected:
            return False

        return self.set_mode("RTL")

    def emergency_land(self) -> bool:
        """Execute emergency landing"""
        if not self.connected:
            return False

        return self.set_mode("LAND")

    def loiter(self) -> bool:
        """Hold position and loiter"""
        if not self.connected:
            return False

        return self.set_mode("LOITER")

    def is_connected(self) -> bool:
        """Check if connection is alive"""
        if not self.master:
            return False

        # Check if heartbeat received recently (within 5 seconds)
        return (time.time() - self.last_heartbeat) < 5.0

    def cleanup(self):
        """Close MAVLink connection"""
        if self.master:
            self.master.close()
            self.connected = False
            self.logger.info("MAVLink connection closed")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Connect to flight controller
    # Use "/dev/ttyACM0" for USB connection
    # Use "udp:127.0.0.1:14550" for SITL simulation
    bridge = MAVLinkBridge("/dev/ttyACM0")

    if bridge.is_connected():
        print("Connected to flight controller")

        # Get telemetry
        for _ in range(10):
            telemetry = bridge.get_telemetry()
            if telemetry:
                print(f"\nTelemetry:")
                print(f"  Position: ({telemetry.latitude:.6f}, {telemetry.longitude:.6f})")
                print(f"  Altitude: {telemetry.altitude:.1f}m")
                print(f"  Battery: {telemetry.battery_remaining}%")
                print(f"  Mode: {telemetry.flight_mode}")
                print(f"  Armed: {telemetry.armed}")

            time.sleep(1)

        # Example commands (commented out for safety)
        # bridge.set_mode("GUIDED")
        # bridge.arm()
        # bridge.goto_waypoint(59.9139, 10.7522, 100)
        # bridge.return_to_launch()

    bridge.cleanup()
