# Multiagent.py
import agentpy as ap
from owlready2 import *
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create ontology
onto = get_ontology("file://onto.owl")

with onto:
    class Agent(Thing):
        pass

    class Camera(Agent):
        pass
    
    class Drone(Agent):
        pass
    
    class Guard(Agent):
        pass
    
    class DetectedObject(Thing):
        pass
    
    class Fugitive(DetectedObject):
        pass
    
    class Mouse(DetectedObject):
        pass
    
    class Position(Thing):
        pass
    
    class Message(Thing):
        pass
    
    class has_x(FunctionalProperty, DataProperty):
        domain = [Position]
        range = [int]
    
    class has_y(FunctionalProperty, DataProperty):
        domain = [Position]
        range = [int]
    
    class has_position(FunctionalProperty, ObjectProperty):
        domain = [Agent, DetectedObject]
        range = [Position]
    
    class has_detected_object(FunctionalProperty, ObjectProperty):
        domain = [Agent]
        range = [DetectedObject]
    
    class has_action(FunctionalProperty, DataProperty):
        domain = [Agent]
        range = [str]
    
    class has_path(FunctionalProperty, DataProperty):
        domain = [Drone]        
        range = [str]
    
    class has_vision_radius(FunctionalProperty, DataProperty):
        domain = [Agent]
        range = [int]
    
    class has_sender(ObjectProperty):
        domain = [Message]
        range = [Agent]
    
    class has_receiver(ObjectProperty):
        domain = [Message]
        range = [Agent]
    
    class has_content(DataProperty):
        domain = [Message]
        range = [str]
    
    class has_environment(DataProperty):
        domain = [Agent]
        range = [str]

onto.save()

class AgentBase(ap.Agent):
    def setup(self):
        self.agent = None
        self.message_queue = []

    def send_message(self, receiver, content):
        message = onto.Message()
        message.has_sender = self.agent
        message.has_receiver = receiver
        message.has_content = content
        receiver.message_queue.append(message)
        return message

    def receive_messages(self):
        messages = self.message_queue
        self.message_queue = []
        return messages

class CameraAgent(AgentBase):
    def setup(self):
        super().setup()
        self.agent = onto.Camera()
        self.agent.has_vision_radius = 85
    
    def detect(self, data):
        position = onto.Position()
        position.has_x = data['position'][0]
        position.has_y = data['position'][1]
        self.agent.has_position = position
        
        if data['Detect'] > 0:
            detected_object = onto.Fugitive() if data['Detect'] == 2 else onto.Mouse()
            object_position = onto.Position()
            object_position.has_x = data['DetectPosition'][0]
            object_position.has_y = data['DetectPosition'][1]
            detected_object.has_position = object_position
            self.agent.has_detected_object = detected_object
            self.agent.has_action = "alarm"
            return "alarm", self.send_message(onto.Drone, f"Detected object at {data['DetectPosition']}")
        else:
            self.agent.has_detected_object = None
            self.agent.has_action = "ignore"
            return "ignore", None

class GuardAgent(AgentBase):
    def setup(self):
        super().setup()
        self.agent = onto.Guard()
        position = onto.Position()
        position.has_x = 0
        position.has_y = 50
        self.agent.has_position = position
        self.alarm_triggered = False
        self.investigation_target = None

    def process_messages(self):
        messages = self.receive_messages()
        for message in messages:
            if isinstance(message.has_sender, onto.Drone):
                return self.process_drone_info(message.has_content)
        return self.command_drone()

    def process_drone_info(self, drone_info):
        if isinstance(drone_info, onto.Fugitive):
            self.investigation_target = drone_info.has_position
            return self.investigate()
        elif isinstance(drone_info, onto.Mouse):
            # Ignore mice, continue patrolling
            return self.command_drone()
        else:
            # No detection, continue patrolling
            return self.command_drone()

    def investigate(self):
        if self.investigation_target:
            if not self.alarm_triggered:
                self.alarm_triggered = True
                self.agent.has_action = "alarm"
                return "alarm", None
            else:
                return "end_simulation", None
        else:
            return self.command_drone()

    def command_drone(self):
        # Implement patrol logic
        command = "investigate"  # Always ask drone to investigate
        self.send_message(onto.Drone, command)
        return "guard", command

    def find_path(self, start, goal):
        def heuristic(a, b):
            return abs(a.has_x - b.has_x) + abs(a.has_y - b.has_y)
        
        def get_neighbors(position):
            x, y = position.has_x, position.has_y
            neighbors = []
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 100 and 0 <= ny < 100 and self.environment[ny, nx] == 0:
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

    def get_position(self, x, y):
        return self.position_pool.get((x, y))

    def control_drone(self, drone_data):
        # Control the drone using the same logic as DroneAgent
        return self.drone_agent.detect(drone_data)

class DroneAgent(AgentBase):
    def setup(self):
        super().setup()
        self.agent = onto.Drone()
        self.agent.has_vision_radius = 20
        self.agent.has_path = ""
        self.position_pool = {}
        for x in range(100):
            for y in range(100):
                position = onto.Position()
                position.has_x = x
                position.has_y = y
                self.position_pool[(x, y)] = position
        
        self.agent.has_position = self.position_pool[(0, 50)]
        self.target_position = self.get_position(0, 50)
        self.environment = self.create_environment()
        self.agent.has_environment.append(str(self.environment.tolist()))

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

    def move(self):
        current_position = self.agent.has_position
        
        if self.agent.has_detected_object:
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
            self.agent.has_position = next_position
            self.agent.has_path = ",".join(f"{p.has_x},{p.has_y}" for p in path)
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
    
    def execute_guard_command(self, command):
        if command == "investigate":
            return "investigate", self.agent.has_detected_object
        # ... (other commands can be added here)
        return "idle", None

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

    def detect(self, data):
        current_position = self.get_position(data['position'][0], data['position'][1])
        self.agent.has_position = current_position
        
        detected_object = None
        if data['Detect'] > 0:
            detected_object = onto.Fugitive() if data['Detect'] == 2 else onto.Mouse()
            object_position = self.get_position(data['DetectPosition'][0], data['DetectPosition'][1])
            detected_object.has_position = object_position
            self.agent.has_detected_object = detected_object
        
        messages = self.receive_messages()
        for message in messages:
            if isinstance(message.has_sender, onto.Guard):
                return self.execute_guard_command(message.has_content)
        
        return self.move(), detected_object
    
class MultiAgentSystem:
    def __init__(self):
        self.model = ap.Model()
        self.setup()
        self.grid = self.create_environment()
        self.simulation_phase = "camera"

    def setup(self):
        self.camera_agents = {}
        for i in range(4):
            agent = CameraAgent(self.model)
            self.camera_agents[i] = agent
        self.drone_agent = DroneAgent(self.model)
        self.guard_agent = GuardAgent(self.model)

    def create_environment(self):
        return self.drone_agent.environment

    def process_detection(self, camera_data, drone_data):
        if self.simulation_phase == "camera":
            return self.process_camera_phase(camera_data)
        elif self.simulation_phase == "drone":
            return self.process_drone_phase(drone_data)
        elif self.simulation_phase == "guard":
            return self.process_guard_phase(drone_data)

    def process_camera_phase(self, camera_data):
        camera_results = []
        for camera_info in camera_data:
            camera_id = camera_info['id']
            if camera_id in self.camera_agents:
                action, message = self.camera_agents[camera_id].detect(camera_info)
                camera_results.append({"id": camera_id, "action": action})
                if action == "alarm":
                    self.simulation_phase = "drone"
        
        if self.simulation_phase == "drone":
            drone_action, drone_direction = self.drone_agent.detect({"position": [0, 50], "Detect": 0})
        else:
            drone_action, drone_direction = "idle", None

        return camera_results, {"action": drone_action, "direction": drone_direction}

    def process_drone_phase(self, drone_data):
        drone_action, drone_direction = self.drone_agent.detect(drone_data)
        if drone_action == "end_drone_phase":
            self.simulation_phase = "guard"
            guard_action, guard_command = self.guard_agent.process_messages()
            return [], {"action": "guard", "command": guard_command}
        return [], {"action": drone_action, "direction": drone_direction}

    def process_guard_phase(self, drone_data):
        guard_action, guard_command = self.guard_agent.process_messages()
        if guard_action == "alarm":
            return [], {"action": "end_simulation"}
        else:
            drone_action, drone_direction = self.drone_agent.detect(drone_data)
            return [], {"action": guard_action, "direction": drone_direction}

def main():
    mas = MultiAgentSystem()

if __name__ == "__main__":
    main()