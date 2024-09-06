import agentpy as ap
from owlready2 import *
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create ontology
onto = get_ontology("http://example.org/surveillance_ontology.owl")

with onto:
    class Camera(Thing):
        pass
    
    class Drone(Thing):
        pass
    
    class DetectedObject(Thing):
        pass
    
    class Fugitive(DetectedObject):
        pass
    
    class Mouse(DetectedObject):
        pass
    
    class Position(Thing):
        pass
    
    class has_x(FunctionalProperty, DataProperty):
        domain = [Position]
        range = [int]
    
    class has_y(FunctionalProperty, DataProperty):
        domain = [Position]
        range = [int]
    
    class has_position(FunctionalProperty, ObjectProperty):
        domain = [Camera, Drone, DetectedObject]
        range = [Position]
    
    class has_detected_object(FunctionalProperty, ObjectProperty):
        domain = [Camera, Drone]
        range = [DetectedObject]
    
    class has_action(FunctionalProperty, DataProperty):
        domain = [Camera, Drone]
        range = [str]
    
    class has_path(FunctionalProperty, DataProperty):
        domain = [Drone]
        range = [str]
    
    class has_vision_radius(FunctionalProperty, DataProperty):
        domain = [Camera, Drone]
        range = [int]

class CameraAgent(ap.Agent):
    def setup(self):
        self.camera = onto.Camera()
        self.camera_id = self.id
        self.camera.has_vision_radius = 85
    
    def detect(self, data):
        position = onto.Position()
        position.has_x = data['position'][0]
        position.has_y = data['position'][1]
        self.camera.has_position = position
        
        if data['Detect'] > 0:
            detected_object = onto.Fugitive() if data['Detect'] == 2 else onto.Mouse()
            object_position = onto.Position()
            object_position.has_x = data['DetectPosition'][0]
            object_position.has_y = data['DetectPosition'][1]
            detected_object.has_position = object_position
            self.camera.has_detected_object = detected_object
            self.camera.has_action = "alarm"
            return "alarm", detected_object
        else:
            self.camera.has_detected_object = None
            self.camera.has_action = "ignore"
            return "ignore", None

class DroneAgent(ap.Agent):
    def setup(self):
        self.drone = onto.Drone()
        self.position_pool = {}
        for x in range(100):
            for y in range(100):
                position = onto.Position()
                position.has_x = x
                position.has_y = y
                self.position_pool[(x, y)] = position
        
        self.drone.has_position = self.position_pool[(0, 50)]
        self.drone.has_vision_radius = 20
        self.drone.has_path = ""
        self.target_position = None
        self.environment = self.create_environment()

    def create_environment(self):
        env = np.zeros((100, 100))
        columns = [
            (10, 0, 90, 10),   # Column 1 (from top)
            (30, 10, 100, 10), # Column 2 (from bottom)
            (60, 10, 100, 10), # Column 3 (from bottom)
            (80, 0, 90, 10),   # Column 4 (from top)
        ]
        for col, start, end, width in columns:
            env[start:end, col:col+width] = 1
        return env

    def get_position(self, x, y):
        return self.position_pool.get((x, y))
    
    def set_target_position(self, x, y):
        self.target_position = self.get_position(x, y)
        logger.info(f"Drone target set to: ({x}, {y})")

    def move(self, grid):
        current_position = self.drone.has_position
        logger.info(f"Drone current position: ({current_position.has_x}, {current_position.has_y})")
        
        if self.drone.has_detected_object:
            target = self.get_position(0, 50)
            logger.info("Drone has detected object, returning to start")
        elif self.target_position:
            target = self.target_position
            logger.info(f"Drone moving towards target: ({target.has_x}, {target.has_y})")
        else:
            logger.info("No target set for drone, staying in place")
            return "stay", None
        
        path = self.find_path(current_position, target)
        if path and len(path) > 1:
            next_position = path[1]  # First step in the path
            self.drone.has_position = next_position
            self.drone.has_path = ",".join(f"{p.has_x},{p.has_y}" for p in path)
            direction = self.get_direction(current_position, next_position)
            logger.info(f"Drone moving {direction} to ({next_position.has_x}, {next_position.has_y})")
            return "move", direction
        logger.info("No path found or already at target, drone staying in place")
        return "stay", None
    
    def find_path(self, start, goal):
        def heuristic(a, b):
            return abs(a.has_x - b.has_x) + abs(a.has_y - b.has_y)
        
        def get_neighbors(position):
            x, y = position.has_x, position.has_y
            neighbors = []
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 100 and 0 <= ny < 100 and self.environment[ny, nx] == 0:  # Note the [y, x] indexing
                    neighbors.append(self.get_position(nx, ny))
            return neighbors
        
        open_set = [start]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, goal)}
        
        while open_set:
            current = min(open_set, key=lambda p: f_score[p])
            if current.has_x == goal.has_x and current.has_y == goal.has_y:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return list(reversed(path))
            
            open_set.remove(current)
            for neighbor in get_neighbors(current):
                tentative_g_score = g_score[current] + 1
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + heuristic(neighbor, goal)
                    if neighbor not in open_set:
                        open_set.append(neighbor)
        
        logger.warning(f"No path found from ({start.has_x}, {start.has_y}) to ({goal.has_x}, {goal.has_y})")
        return None
    
    def get_direction(self, current, next):
        dx = next.has_x - current.has_x
        dy = next.has_y - current.has_y
        if dx == 1:
            return "right"
        elif dx == -1:
            return "left"
        elif dy == 1:
            return "down"  # Changed from "up" to "down"
        elif dy == -1:
            return "up"  # Changed from "down" to "up"
        else:
            return None
    
    def detect(self, data, grid):
        position = self.get_position(data['position'][0], data['position'][1])
        self.drone.has_position = position
        
        if data['Detect'] > 0:
            detected_object = onto.Fugitive() if data['Detect'] == 2 else onto.Mouse()
            object_position = self.get_position(self.target_position.has_x, self.target_position.has_y)
            detected_object.has_position = object_position
            self.drone.has_detected_object = detected_object
            
            if position.has_x == 0 and position.has_y == 50:
                return "end_simulation", None
            else:
                return self.move(grid)
        else:
            self.drone.has_detected_object = None
            return self.move(grid)

class MultiAgentSystem:
    def __init__(self):
        self.model = ap.Model()
        self.setup()
        self.grid = np.zeros((100, 100))
    
    def setup(self):
        self.camera_agents = {}
        for i in range(4):
            agent = CameraAgent(self.model)
            self.camera_agents[i] = agent
        self.drone_agent = DroneAgent(self.model)
    
    def process_detection(self, camera_data, drone_data):
        camera_results = []
        if camera_data:
            for camera_info in camera_data:
                camera_id = camera_info['id']
                if camera_id in self.camera_agents:
                    action, detected_object = self.camera_agents[camera_id].detect(camera_info)
                    camera_results.append({"id": camera_id, "action": action})
                    if detected_object:
                        # Set the target position for the drone
                        detect_x, detect_y = camera_info['DetectPosition']
                        absolute_x = camera_info['position'][0] + detect_x
                        absolute_y = camera_info['position'][1] + detect_y
                        self.drone_agent.set_target_position(absolute_x, absolute_y)
                        logger.info(f"Camera {camera_id} detected object at ({absolute_x}, {absolute_y})")
        
        if drone_data:
            drone_action, drone_direction = self.drone_agent.detect(drone_data, self.drone_agent.environment)
        else:
            drone_action, drone_direction = "idle", None
        
        return camera_results, drone_action, drone_direction
    
def main():
    mas = MultiAgentSystem()
    # Add test code here if needed

if __name__ == "__main__":
    main()