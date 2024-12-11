from pyray import *
import random
from enum import Enum

# Constants
LANE_WIDTH = 4.0
NUM_LANES = 2
LANE_POSITIONS = {
    'x': [-LANE_WIDTH/2, LANE_WIDTH/2],
    'z': [-LANE_WIDTH/2, LANE_WIDTH/2]
}

class LightState(Enum):
    RED = 1
    YELLOW = 2
    GREEN = 3

class TrafficLight:
    def __init__(self):
        self.timer = 0
        self.switch_interval = 180  # 3 seconds at 60 FPS
        self.yellow_duration = 60   # 1 second at 60 FPS
        self.x_axis_state = LightState.GREEN
        self.z_axis_state = LightState.RED
        self.changing_to_red = False

    def update(self):
        self.timer += 1
        if self.changing_to_red:
            if self.timer >= self.yellow_duration:
                self.timer = 0
                self.changing_to_red = False
                if self.x_axis_state == LightState.YELLOW:
                    self.x_axis_state = LightState.RED
                    self.z_axis_state = LightState.GREEN
                else:
                    self.x_axis_state = LightState.GREEN
                    self.z_axis_state = LightState.RED
        elif self.timer >= self.switch_interval:
            self.timer = 0
            self.changing_to_red = True
            if self.x_axis_state == LightState.GREEN:
                self.x_axis_state = LightState.YELLOW
            else:
                self.z_axis_state = LightState.YELLOW

    def draw(self):
        # X-axis lights
        light_color = GREEN if self.x_axis_state == LightState.GREEN else \
                     YELLOW if self.x_axis_state == LightState.YELLOW else RED
        draw_sphere(Vector3(15, 5, 0), 1, light_color)
        draw_sphere(Vector3(-15, 5, 0), 1, light_color)
        
        # Z-axis lights
        light_color = GREEN if self.z_axis_state == LightState.GREEN else \
                     YELLOW if self.z_axis_state == LightState.YELLOW else RED
        draw_sphere(Vector3(0, 5, 15), 1, light_color)
        draw_sphere(Vector3(0, 5, -15), 1, light_color)

class Car:
    def __init__(self, position, movement):
        self.position = position
        self.movement = movement
        self.stopped = False
        self.safe_distance = 5.0
        self.stop_reason = ""
        self.speed = 0.2
        self.width = 2.0
        self.height = 1.5
        self.length = 4.0
        
        # Set color based on direction
        if movement.x > 0:
            self.color = BLUE
        elif movement.x < 0:
            self.color = RED
        elif movement.z > 0:
            self.color = GREEN
        else:
            self.color = YELLOW

    def update(self, traffic_light, other_cars):
        should_stop = False
        self.stop_reason = ""
        
        # Traffic light check
        if abs(self.movement.x) > 0:  # X-axis movement
            if self.movement.x > 0:  # Moving right
                approaching_junction = -12 < self.position.x < 0
            else:  # Moving left
                approaching_junction = 0 < self.position.x < 12
            
            # Only stop if approaching and light isn't green
            if approaching_junction:
                if traffic_light.x_axis_state == LightState.RED:
                    should_stop = True
                    self.stop_reason = "RED"
                elif traffic_light.x_axis_state == LightState.YELLOW:
                    if abs(self.position.x) > 6:  # Only stop for yellow if not too close
                        should_stop = True
                        self.stop_reason = "YELLOW"

        else:  # Z-axis movement
            if self.movement.z > 0:  # Moving forward
                approaching_junction = -12 < self.position.z < 0
            else:  # Moving backward
                approaching_junction = 0 < self.position.z < 12
            
            if approaching_junction:
                if traffic_light.z_axis_state == LightState.RED:
                    should_stop = True
                    self.stop_reason = "RED"
                elif traffic_light.z_axis_state == LightState.YELLOW:
                    if abs(self.position.z) > 6:
                        should_stop = True
                        self.stop_reason = "YELLOW"

        # Check for cars ahead
        if not should_stop:
            for other_car in other_cars:
                if other_car == self:
                    continue
                
                same_lane = False
                car_ahead = False
                
                if abs(self.movement.x) > 0:
                    same_lane = abs(self.position.z - other_car.position.z) < 1.0
                    car_ahead = (self.movement.x > 0 and other_car.position.x > self.position.x) or \
                               (self.movement.x < 0 and other_car.position.x < self.position.x)
                else:
                    same_lane = abs(self.position.x - other_car.position.x) < 1.0
                    car_ahead = (self.movement.z > 0 and other_car.position.z > self.position.z) or \
                               (self.movement.z < 0 and other_car.position.z < self.position.z)
                
                if same_lane and car_ahead:
                    dist = ((self.position.x - other_car.position.x) ** 2 + 
                           (self.position.z - other_car.position.z) ** 2) ** 0.5
                    if dist < self.safe_distance:
                        should_stop = True
                        self.stop_reason = "CAR AHEAD"
                        break

        # Update movement
        if not should_stop:
            self.position.x += self.movement.x * self.speed
            self.position.z += self.movement.z * self.speed
            self.stopped = False
        else:
            self.stopped = True

    def draw(self, camera):
        # Draw car body
        if abs(self.movement.x) > 0:
            draw_cube(self.position, self.length, self.height, self.width, self.color)
            draw_cube_wires(self.position, self.length, self.height, self.width, BLACK)
        else:
            draw_cube(self.position, self.width, self.height, self.length, self.color)
            draw_cube_wires(self.position, self.width, self.height, self.length, BLACK)

        # Draw stop reason if stopped
        if self.stopped:
            pos2d = get_world_to_screen(
                Vector3(self.position.x, self.position.y + 2, self.position.z),
                camera
            )
            draw_text(self.stop_reason, int(pos2d.x), int(pos2d.y), 20, RED)

def draw_lanes():
    lane_length = 50.0
    lane_color = GRAY
    
    for z in LANE_POSITIONS['x']:
        start = Vector3(-lane_length, 0.1, z - LANE_WIDTH/2)
        end = Vector3(lane_length, 0.1, z - LANE_WIDTH/2)
        draw_line_3d(start, end, lane_color)
        start = Vector3(-lane_length, 0.1, z + LANE_WIDTH/2)
        end = Vector3(lane_length, 0.1, z + LANE_WIDTH/2)
        draw_line_3d(start, end, lane_color)

    for x in LANE_POSITIONS['z']:
        start = Vector3(x - LANE_WIDTH/2, 0.1, -lane_length)
        end = Vector3(x - LANE_WIDTH/2, 0.1, lane_length)
        draw_line_3d(start, end, lane_color)
        start = Vector3(x + LANE_WIDTH/2, 0.1, -lane_length)
        end = Vector3(x + LANE_WIDTH/2, 0.1, lane_length)
        draw_line_3d(start, end, lane_color)

def spawn_car(direction='x'):
    if direction == 'x':
        pos = Vector3(-20.0, 2.0, LANE_POSITIONS['x'][0])
        movement = Vector3(1.0, 0.0, 0.0)
    elif direction == '-x':
        pos = Vector3(20.0, 2.0, LANE_POSITIONS['x'][1])
        movement = Vector3(-1.0, 0.0, 0.0)
    elif direction == 'z':
        pos = Vector3(LANE_POSITIONS['z'][0], 2.0, -20.0)
        movement = Vector3(0.0, 0.0, 1.0)
    else:  # '-z'
        pos = Vector3(LANE_POSITIONS['z'][1], 2.0, 20.0)
        movement = Vector3(0.0, 0.0, -1.0)
    return Car(pos, movement)

def main():
    # Initialize window
    set_config_flags(FLAG_MSAA_4X_HINT)
    init_window(800, 600, "Traffic Simulation")
    set_target_fps(60)

    # Camera setup
    camera = Camera3D()
    camera.position = Vector3(40.0, 40.0, 40.0)
    camera.target = Vector3(0.0, 0.0, 0.0)
    camera.up = Vector3(0.0, 1.0, 0.0)
    camera.fovy = 45.0
    camera.projection = CAMERA_PERSPECTIVE

    # Game objects
    cars = []
    traffic_light = TrafficLight()
    MAX_CARS = 12
    SPAWN_CHANCE = 0.01

    # Main game loop
    while not window_should_close():
        # Update
        traffic_light.update()
        
        # Random car spawning
        if len(cars) < MAX_CARS and random.random() < SPAWN_CHANCE:
            direction = random.choice(['x', '-x', 'z', '-z'])
            cars.append(spawn_car(direction))

        # Update all cars
        for car in cars:
            car.update(traffic_light, cars)

        # Remove out-of-bounds cars
        cars = [car for car in cars if abs(car.position.x) < 50.0 and abs(car.position.z) < 50.0]

        # Draw
        begin_drawing()
        clear_background(RAYWHITE)
        
        begin_mode_3d(camera)
        draw_grid(20, 1.0)
        draw_lanes()
        traffic_light.draw()
        for car in cars:
            car.draw(camera)
        end_mode_3d()

        # Draw UI with debug info
        draw_fps(10, 10)
        draw_text(f"Cars: {len(cars)}", 10, 30, 20, DARKGRAY)
        draw_text(f"X-axis: {traffic_light.x_axis_state.name}", 10, 50, 20, DARKGRAY)
        draw_text(f"Z-axis: {traffic_light.z_axis_state.name}", 10, 70, 20, DARKGRAY)
        draw_text(f"Timer: {traffic_light.timer}", 10, 90, 20, DARKGRAY)
        draw_text(f"Changing: {traffic_light.changing_to_red}", 10, 110, 20, DARKGRAY)
        
        end_drawing()

    close_window()

if __name__ == "__main__":
    main()