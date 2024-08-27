import agentpy as ap
import numpy as np
import json
import random   

class Robot(ap.Agent):
    def setup(self):
        self.id = None
        self.position = None
        self.movements = 0
        self.isHolding = False
        self.state = {
            "position": None,
            "isHolding": False,
            "perception": {"F": 0, "B": 0, "L": 0, "R": 0}
        }

    def update_state(self, perception_json):
        # Update the robot's state based on the received JSON
        perception = json.loads(perception_json)
        self.id = perception["id"]
        self.state["perception"] = perception["position"]
        self.state["isHolding"] = self.isHolding

    def perception(self):
        perception = self.state["perception"]
        
        # Check if all values are 0 (no obstacles)
        if all(value == 0 for value in perception.values()):
            return "move_random"
        
        # Check for boxes (1) and grab one if found
        boxes = [direction for direction, value in perception.items() if value == 1]
        if boxes and not self.isHolding:
            chosen_direction = random.choice(boxes)
            self.isHolding = True
            return f"grab_{chosen_direction}"
        
        # Check for obstacles (2) and avoid them
        obstacles = [direction for direction, value in perception.items() if value == 2]
        if obstacles:
            available_directions = [d for d in ["F", "B", "L", "R"] if d not in obstacles]
            if available_directions:
                return f"move_{random.choice(available_directions)}"
            else:
                return "wait"  # All directions blocked
        
        # Check for box stacks (3)
        box_stacks = [direction for direction, value in perception.items() if value == 3]
        if box_stacks:
            if self.isHolding:
                chosen_direction = random.choice(box_stacks)
                self.isHolding = False
                return f"drop_{chosen_direction}"
            else:
                # Treat as obstacle if not holding a box
                available_directions = [d for d in ["F", "B", "L", "R"] if d not in box_stacks]
                if available_directions:
                    return f"move_{random.choice(available_directions)}"
                else:
                    return "wait"  # All directions blocked
        
        # If none of the above conditions are met, move randomly
        return "move_random"

    def act(self, action):
        if action.startswith("move_"):
            self.movements += 1
        return action

    def reason(self):
        # The perception function now acts as the reasoning component
        action = self.perception()
        return json.dumps({"action": action})

    def step(self, perception_json):
        self.update_state(perception_json)
        action_json = self.reason()
        action = json.loads(action_json)["action"]
        return self.act(action)

class ObjectStackingModel(ap.Model):
    def setup(self):
        # Initialize model parameters
        self.num_robots = 5
        self.num_objects = self.p.num_objects
        self.grid_size = self.p.grid_size
        self.max_steps = self.p.max_steps
        self.current_step = 0

        # Create grid
        self.grid = ap.Grid(self, (self.grid_size, self.grid_size), track_empty=True)

        # Create robots
        self.robots = ap.AgentList(self, self.num_robots, Robot)
        for i, robot in enumerate(self.robots):
            robot.id = i + 1  # Assign ID to each robot
        self.grid.add_agents(self.robots, random=True, empty=True)

        # Create objects
        self.objects = ap.AgentList(self, self.num_objects, ap.Agent)
        self.grid.add_agents(self.objects, random=True, empty=True)

        # Initialize stacks
        self.stacks = {}

        # Data collection
        self.data = {
            'steps_to_completion': None,
            'robot_movements': {robot.id: 0 for robot in self.robots}
        }

    def get_perception(self, robot):
        # Get the robot's current position
        x, y = self.grid.positions[robot]

        # Define the four directions
        directions = {'F': (0, 1), 'B': (0, -1), 'L': (-1, 0), 'R': (1, 0)}

        perception = {}
        for direction, (dx, dy) in directions.items():
            new_x, new_y = x + dx, y + dy
            
            # Check if the new position is within the grid
            if 0 <= new_x < self.grid_size and 0 <= new_y < self.grid_size:
                cell_content = self.grid[new_x, new_y]
                if not cell_content:
                    perception[direction] = 0  # Empty
                elif any(isinstance(agent, Robot) for agent in cell_content):
                    perception[direction] = 2  # Obstacle (treating other robots as obstacles)
                elif len(cell_content) == 1:
                    perception[direction] = 1  # Single box
                else:
                    perception[direction] = 3  # Box stack
            else:
                perception[direction] = 2  # Treat out-of-bounds as an obstacle

        return json.dumps({
            "id": robot.id,
            "position": perception
        })

    def update_environment(self, robot, action):
        if action.startswith("move_"):
            direction = action.split("_")[1]
            if direction == "random":
                direction = random.choice(['F', 'B', 'L', 'R'])
            
            dx, dy = {'F': (0, 1), 'B': (0, -1), 'L': (-1, 0), 'R': (1, 0)}[direction]
            current_pos = self.grid.positions[robot]
            new_pos = (current_pos[0] + dx, current_pos[1] + dy)
            
            if self.grid.empty[new_pos]:
                self.grid.move_to(robot, new_pos)
                self.data['robot_movements'][robot.id] += 1

        elif action.startswith("grab_"):
            direction = action.split("_")[1]
            dx, dy = {'F': (0, 1), 'B': (0, -1), 'L': (-1, 0), 'R': (1, 0)}[direction]
            current_pos = self.grid.positions[robot]
            grab_pos = (current_pos[0] + dx, current_pos[1] + dy)
            
            objects_at_pos = [agent for agent in self.grid[grab_pos] if agent in self.objects]
            if objects_at_pos:
                grabbed_object = objects_at_pos[0]
                self.grid.remove_agents(grabbed_object)
                robot.isHolding = True

        elif action.startswith("drop_"):
            direction = action.split("_")[1]
            dx, dy = {'F': (0, 1), 'B': (0, -1), 'L': (-1, 0), 'R': (1, 0)}[direction]
            current_pos = self.grid.positions[robot]
            drop_pos = (current_pos[0] + dx, current_pos[1] + dy)
            
            if robot.isHolding:
                new_object = ap.Agent(self)
                self.grid.add_agents(new_object, positions=drop_pos)
                self.objects.append(new_object)
                robot.isHolding = False

                # Update stacks
                if drop_pos not in self.stacks:
                    self.stacks[drop_pos] = 1
                else:
                    self.stacks[drop_pos] += 1

    def step(self):
        self.current_step += 1

        for robot in self.robots:
            perception_json = self.get_perception(robot)
            action = robot.step(perception_json)
            self.update_environment(robot, action)

        # Check if simulation should end
        if self.check_end_condition():
            if self.data['steps_to_completion'] is None:
                self.data['steps_to_completion'] = self.current_step
            self.stop()

    def check_end_condition(self):
        # Check if all objects are in stacks of maximum 5
        return all(1 <= stack_size <= 5 for stack_size in self.stacks.values()) and \
               sum(self.stacks.values()) == self.num_objects

    def end(self):
        # If simulation ended due to max steps, record that
        if self.data['steps_to_completion'] is None:
            self.data['steps_to_completion'] = self.max_steps

        print(f"Simulation ended after {self.data['steps_to_completion']} steps")
        print("Robot movements:")
        for robot_id, movements in self.data['robot_movements'].items():
            print(f"Robot {robot_id}: {movements} movements")

        # Here you could add more detailed analysis or data export

def run_model(parameters):
    model = ObjectStackingModel(parameters)
    results = model.run()
    return model, results

if __name__ == "__main__":
    parameters = {
        'num_objects': 20,
        'grid_size': 10,
        'max_steps': 1000
    }
    model, results = run_model(parameters)