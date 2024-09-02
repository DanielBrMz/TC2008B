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

class Rule:
    def __init__(self, condition, action):
        self.condition = condition
        self.action = action

class AgentBase(ap.Agent):
    def setup(self):
        self.agent = None
        self.message_queue = []

    def set_drone_agent(self, drone_agent):
        self.drone_agent = drone_agent

    def set_guard_agent(self, guard_agent):
        self.guard_agent = guard_agent

    def see(self, data):
        # Implementación base del método see
        self.percepts = data

    def send_message(self, receiver, content):
        message = onto.Message()
        message.has_sender.append(self.agent)
        message.has_receiver.append(receiver)
        message.has_content.append(content)
        receiver.owner.message_queue.append(message)
        return message

    def receive_messages(self):
        messages = self.message_queue
        self.message_queue = []
        return messages

    def receive_messages(self):
        messages = self.message_queue
        self.message_queue = []
        return messages

class CameraAgent(AgentBase):
    def setup(self):
        super().setup()
        self.agent = onto.Camera()
        self.agent.has_vision_radius = 85
        self.percepts = None

    def see(self, data):
        super().see(data)
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
        else:
            self.agent.has_detected_object = None


    def act(self):
        if isinstance(self.agent.has_detected_object, onto.Fugitive):
            return "alarm", self.detect_fugitive()
        elif isinstance(self.agent.has_detected_object, onto.Mouse):
            return "ignore", None
        else:
            return "idle", None

    def detect_fugitive(self):
        fugitive = self.agent.has_detected_object
        return self.send_message(self.drone_agent.agent, f"Detected fugitive at {fugitive.has_position.has_x}, {fugitive.has_position.has_y}")

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
        self.setup_environment()
        self.percepts = None
        self.messages = []

        # Definir reglas basadas en la ontología
        self.rules = [
            Rule(
                lambda: isinstance(self.investigation_target, onto.Position) and not self.alarm_triggered,
                lambda: (self.set_action("alarm"), self.trigger_alarm())
            ),
            Rule(
                lambda: isinstance(self.investigation_target, onto.Position) and self.alarm_triggered,
                lambda: (self.set_action("end_simulation"), self.end_simulation())
            ),
            Rule(
                lambda: any(isinstance(m.has_content, onto.Fugitive) for m in self.messages),
                lambda: (self.set_action("investigate"), self.investigate_fugitive())
            ),
            Rule(
                lambda: any(isinstance(m.has_content, onto.Mouse) for m in self.messages),
                lambda: (self.set_action("ignore"), self.ignore_mouse())
            ),
            Rule(
                lambda: True,  # Default rule
                lambda: (self.set_action("patrol"), self.patrol())
            )
        ]

    def setup_environment(self):
        self.position_pool = {}
        for x in range(100):
            for y in range(100):
                position = onto.Position()
                position.has_x = x
                position.has_y = y
                self.position_pool[(x, y)] = position
        
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

    def see(self, data):
        self.percepts = data
        self.messages = self.receive_messages()

    def next(self):
        for rule in self.rules:
            if rule.condition():
                return rule.action

    def act(self):
        action = self.next()
        if action:
            return action()
        return None, None

    def set_action(self, action):
        self.agent.has_action = action

    def trigger_alarm(self):
        logger.info("Guard is triggering the alarm")
        self.alarm_triggered = True
        return "alarm", None

    def end_simulation(self):
        logger.info("Guard is ending the simulation")
        return "end_simulation", None

    def investigate_fugitive(self):
        logger.info("Guard is investigating a fugitive")
        for message in self.messages:
            if isinstance(message.has_content, onto.Fugitive):
                self.investigation_target = message.has_content.has_position
                break
        return self.investigate()

    def ignore_mouse(self):
        logger.info("Guard is ignoring a mouse")
        return self.command_drone()

    def patrol(self):
        logger.info("Guard is patrolling")
        return self.command_drone()

    def investigate(self):
        if self.investigation_target:
            if not self.alarm_triggered:
                self.alarm_triggered = True
                self.agent.has_action = "alarm"
                logger.info("Guard has triggered the alarm")
                return "alarm", None
            else:
                logger.info("Guard is ending the simulation after investigation")
                return "end_simulation", None
        else:
            logger.info("Guard found no investigation target, continuing patrol")
            return self.command_drone()

    def command_drone(self):
        command = "investigate"  # Always ask drone to investigate
        self.send_message(onto.Drone, command)
        logger.info(f"Guard is commanding the drone to {command}")
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
        logger.info("Guard is controlling the drone")
        
        # Analyze drone data
        if isinstance(drone_data, onto.Fugitive):
            command = "investigate"
            target = drone_data.has_position
        elif isinstance(drone_data, onto.Mouse):
            command = "ignore"
            target = None
        else:
            command = "patrol"
            target = self.get_random_position()  # Implement this method to get a random position

        # Send command to drone
        self.send_command_to_drone(command, target)
        
        return command, target

    def send_command_to_drone(self, command, target):
        message = onto.Message()
        message.has_sender = self.agent
        message.has_receiver = self.drone_agent.agent
        message.has_content = {
            "command": command,
            "target": target
        }
        logger.info(f"Guard sent command to Drone: {command} at {target}")
        self.send_message(self.drone_agent.agent, message.has_content)


    def get_random_position(self):
        valid_positions = []
        for x in range(100):
            for y in range(100):
                if self.environment[y, x] == 0:
                    valid_positions.append(self.get_position(x, y))
        if valid_positions:
            return np.random.choice(valid_positions)
        else:
            logger.warning("No valid positions found in the environment")
            return None

    def process_drone_info(self, drone_info):
        if isinstance(drone_info, onto.Fugitive):
            logger.info("Guard received information about a fugitive from the drone")
            self.investigation_target = drone_info.has_position
            return self.investigate()
        elif isinstance(drone_info, onto.Mouse):
            logger.info("Guard received information about a mouse from the drone")
            return self.command_drone()
        else:
            logger.info("Guard received no significant information from the drone")
            return self.command_drone()

    def receive_messages(self):
        # En una implementación real, aquí se recuperarían los mensajes de una cola o un sistema de mensajería
        # Por ahora, simplemente devolvemos una lista vacía
        return []

    def send_message(self, receiver, content):
        message = onto.Message()
        message.has_sender = self.agent
        message.has_receiver = receiver
        message.has_content = content
        logger.info(f"Guard sent a message to {receiver} with content: {content}")
        # En una implementación real, aquí se enviaría el mensaje a través de un sistema de mensajería
        return message

class DroneAgent(AgentBase):
    def setup(self):
        super().setup()
        self.agent = onto.Drone()
        self.agent.has_vision_radius = 20
        self.agent.has_path = ""
        self.setup_environment()
        self.percepts = None
        self.messages = []

        # Ensure initial position is set
        initial_position = self.get_position(0, 50)
        if initial_position:
            self.agent.has_position = initial_position
            self.target_position = initial_position
            logger.info(f"Drone initial position set to: ({initial_position.has_x}, {initial_position.has_y})")
        else:
            logger.error("Failed to set initial drone position")

        # Definir reglas basadas en la ontología
        self.rules = [
            Rule(
                lambda: isinstance(self.agent.has_detected_object, onto.Fugitive),
                lambda: (self.set_action("investigate"), self.investigate_fugitive())
            ),
            Rule(
                lambda: isinstance(self.agent.has_detected_object, onto.Mouse),
                lambda: (self.set_action("ignore"), self.ignore_mouse())
            ),
            Rule(
                lambda: any(isinstance(m.has_sender, onto.Guard) for m in self.messages),
                lambda: (self.set_action("execute_command"), self.execute_guard_command())
            ),
            Rule(
                lambda: True, 
                lambda: (self.set_action("patrol"), self.patrol())
            )
        ]

    def setup_environment(self):
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
            (10, 0, 90, 10),   # Columna 1
            (30, 10, 100, 10), # Columna 2
            (60, 10, 100, 10), # Columna 3
            (80, 0, 90, 10),   # Columna 4
        ]
        for col, start, end, width in columns:
            env[start:end, col:col+width] = 1
        return env

    def see(self, data):
        super().see(data)
        self.messages = self.receive_messages()

    def process_guard_commands(self):
        for message in self.messages:
            if isinstance(message.has_sender, onto.Guard):
                command = message.has_content["command"]
                target = message.has_content["target"]
                self.execute_command(command, target)
    
    def investigate(self, target):
        self.set_target_position(target.has_x, target.has_y)
        self.agent.has_action = "investigate"

    def ignore(self):
        self.agent.has_action = "ignore"
        self.agent.has_detected_object = None

    def patrol(self, target):
        self.set_target_position(target.has_x, target.has_y)
        self.agent.has_action = "patrol"

    def next(self):
        for rule in self.rules:
            if rule.condition():
                return rule.action

    def act(self):
        action = self.next()
        if action:
            return action()
        return None, None

    def set_action(self, action):
        self.agent.has_action = action

    def investigate_fugitive(self):
        logger.info("Drone is investigating a fugitive")
        return "investigate", self.agent.has_detected_object

    def ignore_mouse(self):
        logger.info("Drone is ignoring a mouse")
        return "ignore", None

    def execute_guard_command(self):
        for message in self.messages:
            if isinstance(message.has_sender, onto.Guard):
                command = message.has_content
                logger.info(f"Drone executing guard command: {command}")
                if command == "investigate":
                    return "investigate", self.agent.has_detected_object
                # ... (other commands can be added here)
        logger.info("No valid guard command, drone staying idle")
        return "idle", None

    def patrol(self):
        logger.info("Drone is patrolling")
        return self.move()

    def move(self):
        current_position = self.agent.has_position
        if not current_position:
            logger.error("Current position is None")
            return "stay", None

        if self.agent.has_detected_object:
            target = self.get_position(0, 50)
            logger.info("Drone has detected object, returning to start")
        elif self.target_position:
            target = self.target_position
            logger.info(f"Drone moving towards target: ({target.has_x}, {target.has_y})")
        else:
            logger.info("No target set for drone, staying in place")
            return "stay", None

        if not target:
            logger.error("Target position is None")
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
        if not start or not goal:
            logger.error(f"Invalid start or goal position. Start: {start}, Goal: {goal}")
            return None

        def heuristic(a, b):
            return abs(a.has_x - b.has_x) + abs(a.has_y - b.has_y)
        
        def get_neighbors(position):
            x, y = position.has_x, position.has_y
            neighbors = []
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 100 and 0 <= ny < 100 and self.environment[ny, nx] == 0:
                    neighbor = self.get_position(nx, ny)
                    if neighbor:
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
        
        logger.warning(f"No path found from ({start.has_x}, {start.has_y}) to ({goal.has_x}, {goal.has_y})")
        return None

    def get_position(self, x, y):
        position = self.position_pool.get((x, y))
        if not position:
            logger.warning(f"Position not found for coordinates: ({x}, {y})")
        return position

    def set_target_position(self, x, y):
        self.target_position = self.get_position(x, y)
        logger.info(f"Drone target set to: ({x}, {y})")

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

    def receive_messages(self):
        # En una implementación real, aquí se recuperarían los mensajes de una cola o un sistema de mensajería
        # Por ahora, simplemente devolvemos una lista vacía
        return []
    
class MultiAgentSystem:
    def __init__(self):
        self.model = ap.Model()
        self.setup()
        self.simulation_phase = "camera"

    def setup(self):
        self.camera_agents = {}
        self.drone_agent = DroneAgent(self.model)
        self.drone_agent.agent = onto.Drone()
        self.drone_agent.agent.owner = self.drone_agent
        self.guard_agent = GuardAgent(self.model)
        self.guard_agent.agent = onto.Guard()
        self.guard_agent.agent.owner = self.guard_agent

        for i in range(4):
            agent = CameraAgent(self.model)
            agent.agent = onto.Camera()
            agent.agent.owner = agent
            agent.set_drone_agent(self.drone_agent)  # Nuevo método
            self.camera_agents[i] = agent

        self.drone_agent.set_guard_agent(self.guard_agent)  # Nuevo método

    def process_detection(self, camera_data, drone_data):
        if self.simulation_phase == "camera":
            return self.process_camera_phase(camera_data)
        elif self.simulation_phase == "drone":
            return self.process_drone_phase(drone_data)
        elif self.simulation_phase == "guard":
            return self.process_guard_phase(drone_data)

    def process_camera_phase(self, camera_data):
        camera_results = []
        drone_action = "idle"
        drone_info = None

        for camera_info in camera_data:
            camera_id = camera_info['id']
            if camera_id in self.camera_agents:
                self.camera_agents[camera_id].see(camera_info)
                action, message = self.camera_agents[camera_id].act()
                camera_results.append({"id": camera_id, "action": action})
                if action == "alarm":
                    self.simulation_phase = "drone"
                    self.drone_agent.see({"position": [0, 50], "Detect": 0, "DetectPosition": None})
                    drone_action, drone_info = self.drone_agent.act()

        return camera_results, {"action": drone_action, "info": drone_info}

    def process_drone_phase(self, drone_data):
        self.drone_agent.see(drone_data)
        drone_action, drone_info = self.drone_agent.act()
        if drone_action == "investigate":
            self.simulation_phase = "guard"
            self.guard_agent.see({"drone_info": drone_info})
            guard_action, guard_info = self.guard_agent.act()
            return [], {"action": guard_action, "info": guard_info}
        return [], {"action": drone_action, "info": drone_info}

    def process_guard_phase(self, drone_data):
        self.drone_agent.see(drone_data)
        drone_action, drone_info = self.drone_agent.act()
        
        # Guard controls the drone
        guard_command, guard_target = self.guard_agent.control_drone(drone_info)
        
        # Update drone with guard's command
        self.drone_agent.see({"guard_command": guard_command, "guard_target": guard_target})
        
        # Get final drone action after processing guard's command
        final_drone_action, final_drone_info = self.drone_agent.act()
        
        if guard_command == "investigate" and isinstance(drone_info, onto.Fugitive):
            return [], {"action": "alarm"}
        elif final_drone_action == "end_simulation":
            return [], {"action": "end_simulation"}
        
        return [], {"action": final_drone_action, "info": final_drone_info}

def main():
    mas = MultiAgentSystem()

if __name__ == "__main__":
    main()