import agentpy as ap
from owlready2 import *
import numpy as np

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
        start_position = onto.Position()
        start_position.has_x = 0
        start_position.has_y = 50
        self.drone.has_position = start_position
        self.drone.has_vision_radius = 20
        self.drone.has_path = ""  # Inicializado como cadena vacía
    
    def move(self, grid):
        current_position = self.drone.has_position
        if self.drone.has_detected_object:
            # Return to start
            target = onto.Position()
            target.has_x = 0
            target.has_y = 50
        else:
            # Move towards the last known position of the detected object
            target = self.model.last_detected_position
        
        path = self.find_path(grid, current_position, target)
        if path:
            next_position = path[1]  # First step in the path
            self.drone.has_position = next_position
            self.drone.has_path = ",".join(f"{p.has_x},{p.has_y}" for p in path)  # Convertir el camino a string
            direction = self.get_direction(current_position, next_position)
            return "move", direction
        return "stay", None
    
    def find_path(self, grid, start, goal):
        # A* pathfinding algorithm
        def heuristic(a, b):
            return abs(a.has_x - b.has_x) + abs(a.has_y - b.has_y)
        
        def get_neighbors(position):
            x, y = position.has_x, position.has_y
            neighbors = []
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 100 and 0 <= ny < 100 and grid[nx][ny] != 1:
                    neighbor = onto.Position()
                    neighbor.has_x = nx
                    neighbor.has_y = ny
                    neighbors.append(neighbor)
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
        
        return None
    
    def get_direction(self, current, next):
        dx = next.has_x - current.has_x
        dy = next.has_y - current.has_y
        if dx == 1:
            return "right"
        elif dx == -1:
            return "left"
        elif dy == 1:
            return "down"
        elif dy == -1:
            return "up"
        else:
            return None
    
    def detect(self, data, grid):
        position = onto.Position()
        position.has_x = data['position'][0]
        position.has_y = data['position'][1]
        self.drone.has_position = position
        
        if data['Detect'] > 0:
            detected_object = onto.Fugitive() if data['Detect'] == 2 else onto.Mouse()
            object_position = onto.Position()
            object_position.has_x = data['DetectPosition'][0]
            object_position.has_y = data['DetectPosition'][1]
            detected_object.has_position = object_position
            self.drone.has_detected_object = detected_object
            
            # Check if drone has returned to start position
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
        self.grid = np.zeros((100, 100))  # Assuming 100x100 grid
        self.last_detected_position = None
    
    def setup(self):
        self.camera_agents = {}
        for i in range(4):
            agent = CameraAgent(self.model)
            self.camera_agents[i] = agent
        self.drone_agent = DroneAgent(self.model)
    
    def process_detection(self, camera_data, drone_data):
        camera_results = []
        for camera_info in camera_data:
            camera_id = camera_info['id']
            if camera_id in self.camera_agents:
                action, detected_object = self.camera_agents[camera_id].detect(camera_info)
                camera_results.append({"id": camera_id, "action": action})
                if detected_object:
                    self.last_detected_position = detected_object.has_position
        
        drone_action, drone_direction = self.drone_agent.detect(drone_data, self.grid)
        
        return camera_results, drone_action, drone_direction

def main():
    mas = MultiAgentSystem()
    # Add test code here if needed

if __name__ == "__main__":
    main()