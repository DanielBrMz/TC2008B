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

        # Create grid
        self.grid = ap.Grid(self, (self.grid_size, self.grid_size), track_empty=True)

        # Create robots
        self.robots = ap.AgentList(self, self.num_robots, Robot)
        self.grid.add_agents(self.robots, random=True, empty=True)

        # Create objects
        self.objects = ap.AgentList(self, self.num_objects, ap.Agent)
        self.grid.add_agents(self.objects, random=True, empty=True)

        # Initialize stacks
        self.stacks = {}

    def step(self):
        for robot in self.robots:
            robot.update_state(self)
            action = robot.reason()
            robot.act(action, self)

        # Check if all objects are in stacks of max 5
        if self.check_stacks():
            self.stop()

    def check_stacks(self):
        # Logic to check if all objects are in stacks of max 5
        pass

    def end(self):
        # Collect and record final data
        pass

def main():
    parameters = {
        'num_objects': 20,
        'grid_size': 10,
        'max_steps': 1000
    }

    model = ObjectStackingModel(parameters)
    results = model.run()
    

if __name__ == "__main__":
    main()