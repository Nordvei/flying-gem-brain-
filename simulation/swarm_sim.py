#!/usr/bin/env python3
"""
Flying GEM Brain - Swarm Simulation
Demonstrates 5-drone autonomous coordination using GEM framework principles
"""

import pygame
import math
import random
from dataclasses import dataclass
from typing import List, Tuple
import sys

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60

# Colors
BACKGROUND = (10, 22, 40)  # Dark navy
DRONE_COLOR = (0, 183, 87)  # Green (active)
DRONE_INACTIVE = (100, 100, 100)  # Gray (inactive)
MESH_LINE = (0, 87, 183, 60)  # Blue transparent
TARGET_COLOR = (255, 215, 0)  # Gold
DETECTION_RADIUS = (255, 0, 0, 30)  # Red transparent
TEXT_COLOR = (255, 255, 255)
GRID_COLOR = (30, 40, 60)

# Drone parameters
DRONE_SPEED = 2.0
SEPARATION_DIST = 100
COHESION_DIST = 200
DETECTION_RANGE = 150
COMMUNICATION_RANGE = 300


@dataclass
class Drone:
    """Represents a single drone in the swarm"""
    id: int
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    active: bool = True
    target_detected: bool = False
    battery: float = 100.0

    def update_position(self):
        """Update drone position based on velocity"""
        self.x += self.vx
        self.y += self.vy

        # Boundary wrap-around
        self.x = self.x % WINDOW_WIDTH
        self.y = self.y % WINDOW_HEIGHT

        # Battery drain
        self.battery = max(0, self.battery - 0.01)
        if self.battery == 0:
            self.active = False

    def distance_to(self, other: 'Drone') -> float:
        """Calculate distance to another drone"""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def distance_to_point(self, x: float, y: float) -> float:
        """Calculate distance to a point"""
        dx = self.x - x
        dy = self.y - y
        return math.sqrt(dx * dx + dy * dy)


class SwarmSimulation:
    """Main simulation class for drone swarm"""

    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Flying GEM Brain - Swarm Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        # Initialize 5 drones in formation
        self.drones = [
            Drone(1, 600, 400, 1, 0),  # Center
            Drone(2, 500, 300, 0.5, 0.5),
            Drone(3, 700, 300, -0.5, 0.5),
            Drone(4, 500, 500, 0.5, -0.5),
            Drone(5, 700, 500, -0.5, -0.5),
        ]

        # Targets to detect
        self.targets = []
        self.spawn_target()

        # Statistics
        self.time_elapsed = 0
        self.detections = 0
        self.messages_sent = 0

        self.running = True

    def spawn_target(self):
        """Spawn a new target at random location"""
        x = random.randint(100, WINDOW_WIDTH - 100)
        y = random.randint(100, WINDOW_HEIGHT - 100)
        self.targets.append((x, y))

    def apply_swarm_behavior(self):
        """Apply GEM-inspired swarm coordination rules"""
        active_drones = [d for d in self.drones if d.active]

        if not active_drones:
            return

        for drone in active_drones:
            # Separation: Avoid crowding neighbors
            sep_x, sep_y = 0, 0

            # Cohesion: Stay close to swarm
            coh_x, coh_y = 0, 0
            coh_count = 0

            # Alignment: Match velocity with neighbors
            align_x, align_y = 0, 0
            align_count = 0

            for other in active_drones:
                if other.id == drone.id:
                    continue

                dist = drone.distance_to(other)

                # Separation
                if dist < SEPARATION_DIST and dist > 0:
                    sep_x += (drone.x - other.x) / dist
                    sep_y += (drone.y - other.y) / dist

                # Cohesion and Alignment
                if dist < COHESION_DIST:
                    coh_x += other.x
                    coh_y += other.y
                    coh_count += 1

                    align_x += other.vx
                    align_y += other.vy
                    align_count += 1

            # Apply cohesion
            if coh_count > 0:
                coh_x /= coh_count
                coh_y /= coh_count
                coh_x = (coh_x - drone.x) * 0.01
                coh_y = (coh_y - drone.y) * 0.01

            # Apply alignment
            if align_count > 0:
                align_x /= align_count
                align_y /= align_count
                align_x *= 0.05
                align_y *= 0.05

            # Target seeking (if target detected by any drone)
            target_x, target_y = 0, 0
            if self.targets and any(d.target_detected for d in active_drones):
                tx, ty = self.targets[0]
                target_x = (tx - drone.x) * 0.02
                target_y = (ty - drone.y) * 0.02

            # Update velocity
            drone.vx += sep_x * 0.1 + coh_x + align_x + target_x
            drone.vy += sep_y * 0.1 + coh_y + align_y + target_y

            # Limit speed
            speed = math.sqrt(drone.vx ** 2 + drone.vy ** 2)
            if speed > DRONE_SPEED:
                drone.vx = (drone.vx / speed) * DRONE_SPEED
                drone.vy = (drone.vy / speed) * DRONE_SPEED

    def check_detections(self):
        """Check if drones detect targets"""
        for drone in self.drones:
            if not drone.active:
                continue

            for i, (tx, ty) in enumerate(self.targets):
                dist = drone.distance_to_point(tx, ty)

                if dist < DETECTION_RANGE:
                    if not drone.target_detected:
                        drone.target_detected = True
                        self.detections += 1
                        self.messages_sent += len([d for d in self.drones if d.active])

                    # Target reached - remove and spawn new one
                    if dist < 30:
                        self.targets.pop(i)
                        self.spawn_target()
                        drone.target_detected = False
                        break

    def draw_grid(self):
        """Draw background grid"""
        for x in range(0, WINDOW_WIDTH, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WINDOW_WIDTH, y))

    def draw_mesh_connections(self):
        """Draw NATS mesh communication lines"""
        active_drones = [d for d in self.drones if d.active]

        for i, drone in enumerate(active_drones):
            for other in active_drones[i + 1:]:
                dist = drone.distance_to(other)
                if dist < COMMUNICATION_RANGE:
                    # Line opacity based on distance
                    opacity = int(255 * (1 - dist / COMMUNICATION_RANGE))
                    color = (*MESH_LINE[:3], min(opacity, 100))

                    surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                    pygame.draw.line(surface, color,
                                   (int(drone.x), int(drone.y)),
                                   (int(other.x), int(other.y)), 1)
                    self.screen.blit(surface, (0, 0))

    def draw_drones(self):
        """Draw all drones"""
        for drone in self.drones:
            color = DRONE_COLOR if drone.active else DRONE_INACTIVE

            # Detection radius
            if drone.active and drone.target_detected:
                surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                pygame.draw.circle(surface, DETECTION_RADIUS,
                                 (int(drone.x), int(drone.y)), DETECTION_RANGE, 2)
                self.screen.blit(surface, (0, 0))

            # Drone body
            pygame.draw.circle(self.screen, color,
                             (int(drone.x), int(drone.y)), 10)

            # Direction indicator
            end_x = drone.x + drone.vx * 15
            end_y = drone.y + drone.vy * 15
            pygame.draw.line(self.screen, color,
                           (int(drone.x), int(drone.y)),
                           (int(end_x), int(end_y)), 2)

            # Drone ID
            id_text = self.small_font.render(f"D{drone.id}", True, TEXT_COLOR)
            self.screen.blit(id_text, (int(drone.x) - 10, int(drone.y) - 25))

            # Battery indicator
            battery_color = (
                int(255 * (1 - drone.battery / 100)),
                int(255 * (drone.battery / 100)),
                0
            )
            pygame.draw.rect(self.screen, battery_color,
                           (int(drone.x) - 10, int(drone.y) + 15,
                            int(20 * drone.battery / 100), 3))

    def draw_targets(self):
        """Draw targets"""
        for tx, ty in self.targets:
            pygame.draw.circle(self.screen, TARGET_COLOR, (int(tx), int(ty)), 8)
            pygame.draw.circle(self.screen, TARGET_COLOR, (int(tx), int(ty)), 12, 2)

    def draw_ui(self):
        """Draw UI elements"""
        active_count = len([d for d in self.drones if d.active])

        info_texts = [
            f"Flying GEM Brain - Swarm Simulation",
            f"",
            f"Active Drones: {active_count}/5",
            f"Operator Ratio: 1:{active_count}",
            f"Detections: {self.detections}",
            f"Mesh Messages: {self.messages_sent}",
            f"Time: {self.time_elapsed:.1f}s",
            f"",
            f"[SPACE] Fail random drone",
            f"[R] Reset simulation",
            f"[ESC] Exit",
        ]

        y_offset = 10
        for text in info_texts:
            surface = self.font.render(text, True, TEXT_COLOR)
            self.screen.blit(surface, (10, y_offset))
            y_offset += 25

    def handle_events(self):
        """Handle user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_SPACE:
                    # Simulate drone failure
                    active = [d for d in self.drones if d.active]
                    if active:
                        random.choice(active).active = False

                if event.key == pygame.K_r:
                    # Reset simulation
                    self.__init__()

    def update(self):
        """Update simulation state"""
        self.apply_swarm_behavior()
        self.check_detections()

        for drone in self.drones:
            if drone.active:
                drone.update_position()

        self.time_elapsed += 1 / FPS

    def draw(self):
        """Draw everything"""
        self.screen.fill(BACKGROUND)
        self.draw_grid()
        self.draw_mesh_connections()
        self.draw_targets()
        self.draw_drones()
        self.draw_ui()
        pygame.display.flip()

    def run(self):
        """Main simulation loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    print("Flying GEM Brain - Swarm Simulation")
    print("====================================")
    print("Demonstrating 5-drone autonomous coordination")
    print("")
    print("Controls:")
    print("  SPACE - Simulate drone failure (test self-healing)")
    print("  R     - Reset simulation")
    print("  ESC   - Exit")
    print("")

    sim = SwarmSimulation()
    sim.run()
