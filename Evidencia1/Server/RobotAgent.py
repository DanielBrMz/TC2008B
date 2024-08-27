import agentpy as ap
import numpy as np
import json
import random
from owlready2 import *

# Create the ontology
onto = get_ontology("http://example.org/robot-ontology.owl")

with onto:
    class Robot(Thing):
        pass

    class Object(Thing):
        pass

    class Position(Thing):
        pass

    class Direction(Thing):
        pass

    class Action(Thing):
        pass

    class has_position = ObjectProperty(domain=Robot, range=Position)
    class is_holding = ObjectProperty(domain=Robot, range=Object)
    class has_perception = ObjectProperty(domain=Robot, range=Direction)
    class can_perform = ObjectProperty(domain=Robot, range=Action)

    class Forward(Direction):
        pass

    class Backward(Direction):
        pass

    class Left(Direction):
        pass

    class Right(Direction):
        pass

    class Move(Action):
        pass

    class Grab(Action):
        pass

    class Drop(Action):
        pass

    class Wait(Action):
        pass

# Save the ontology
onto.save()

class RobotAgent(ap.Agent):
    def setup(self):
        self.onto_robot = onto.Robot()
        self.onto_robot.has_position = [onto.Position()]
        self.movements = 0
        self.rules = [
            ({"perception": {"F": 0, "B": 0, "L": 0, "R": 0}}, "move_random"),
            ({"perception": {"F": 1}, "is_holding": False}, "grab_F"),
            ({"perception": {"B": 1}, "is_holding": False}, "grab_B"),
            ({"perception": {"L": 1}, "is_holding": False}, "grab_L"),
            ({"perception": {"R": 1}, "is_holding": False}, "grab_R"),
            ({"perception": {"F": 3}, "is_holding": True}, "drop_F"),
            ({"perception": {"B": 3}, "is_holding": True}, "drop_B"),
            ({"perception": {"L": 3}, "is_holding": True}, "drop_L"),
            ({"perception": {"R": 3}, "is_holding": True}, "drop_R"),
        ]

    def update_state(self, perception_json):
        perception = json.loads(perception_json)
        self.onto_robot.id = perception["id"]
        for direction, value in perception["position"].items():
            setattr(self.onto_robot, f"has_perception_{direction}", onto[direction](value))
        self.onto_robot.is_holding = [onto.Object()] if self.onto_robot.is_holding else []

    def check_rule(self, rule, state):
        for key, value in rule.items():
            if key == "perception":
                for direction, expected in value.items():
                    if getattr(self.onto_robot, f"has_perception_{direction}").value != expected:
                        return False
            elif key == "is_holding":
                if bool(self.onto_robot.is_holding) != value:
                    return False
        return True

    def perception(self):
        for rule, action in self.rules:
            if self.check_rule(rule, self.onto_robot):
                return action

        # If no rule matches, choose a random direction to move
        return f"move_{random.choice(['F', 'B', 'L', 'R'])}"

    def act(self, action):
        if action.startswith("move_"):
            self.movements += 1
        return action

    def reason(self):
        action = self.perception()
        return json.dumps({"action": action})

    def step(self, perception_json):
        self.update_state(perception_json)
        action_json = self.reason()
        action = json.loads(action_json)["action"]
        return self.act(action)

class ObjectStackingModel(ap.Model):
    def setup(self):
        self.num_robots = 5
        self.num_objects = self.p.num_objects
        self.grid_size = self.p.grid_size
        self.current_step = 0

        self.grid = ap.Grid(self, (self.grid_size, self.grid_size), track_empty=True)

        self.robots = ap.AgentList(self, self.num_robots, RobotAgent)
        for i, robot in enumerate(self.robots):
            robot.onto_robot.id = i + 1
        self.grid.add_agents(self.robots, random=True, empty=True)

        self.objects = ap.AgentList(self, self.num_objects, ap.Agent)
        self.grid.add_agents(self.objects, random=True, empty=True)

        self.stacks = {}

        self.data = {
            'steps_to_completion': None,
            'robot_movements': {robot.onto_robot.id: 0 for robot in self.robots}
        }

    def get_perception(self, robot):
        x, y = self.grid.positions[robot]
        directions = {'F': (0, 1), 'B': (0, -1), 'L': (-1, 0), 'R': (1, 0)}

        perception = {}
        for direction, (dx, dy) in directions.items():
            new_x, new_y = x + dx, y + dy

            if 0 <= new_x < self.grid_size and 0 <= new_y < self.grid_size:
                cell_content = self.grid[new_x, new_y]
                if not cell_content:
                    perception[direction] = 0
                elif any(isinstance(agent, RobotAgent) for agent in cell_content):
                    perception[direction] = 2
                elif len(cell_content) == 1:
                    perception[direction] = 1
                else:
                    perception[direction] = 3
            else:
                perception[direction] = 2

        return json.dumps({
            "id": robot.onto_robot.id,
            "position": perception
        })

    def update_environment(self, robot, action):
        current_pos = self.grid.positions[robot]

        if action.startswith("move_"):
            direction = action.split("_")[1]
            if direction == "random":
                direction = random.choice(['F', 'B', 'L', 'R'])

            dx, dy = {'F': (0, 1), 'B': (0, -1), 'L': (-1, 0), 'R': (1, 0)}[direction]
            new_pos = (current_pos[0] + dx, current_pos[1] + dy)

            if (0 <= new_pos[0] < self.grid_size and 
                0 <= new_pos[1] < self.grid_size and 
                len(self.grid.agents[new_pos]) == 0):
                self.grid.move_to(robot, new_pos)
                self.data['robot_movements'][robot.onto_robot.id] += 1

        elif action.startswith("grab_"):
            direction = action.split("_")[1]
            dx, dy = {'F': (0, 1), 'B': (0, -1), 'L': (-1, 0), 'R': (1, 0)}[direction]
            grab_pos = (current_pos[0] + dx, current_pos[1] + dy)

            if (0 <= grab_pos[0] < self.grid_size and 
                0 <= grab_pos[1] < self.grid_size):
                objects_at_pos = [agent for agent in self.grid.agents[grab_pos] if agent in self.objects]
                if objects_at_pos:
                    grabbed_object = objects_at_pos[0]
                    self.grid.remove_agents(grabbed_object)
                    robot.onto_robot.is_holding = [onto.Object()]

        elif action.startswith("drop_"):
            direction = action.split("_")[1]
            dx, dy = {'F': (0, 1), 'B': (0, -1), 'L': (-1, 0), 'R': (1, 0)}[direction]
            drop_pos = (current_pos[0] + dx, current_pos[1] + dy)

            if (0 <= drop_pos[0] < self.grid_size and 
                0 <= drop_pos[1] < self.grid_size and 
                robot.onto_robot.is_holding):
                new_object = ap.Agent(self)
                self.grid.add_agents(new_object, positions=[drop_pos])
                self.objects.append(new_object)
                robot.onto_robot.is_holding = []

                stack_key = f"{drop_pos[0]},{drop_pos[1]}"
                if stack_key not in self.stacks:
                    self.stacks[stack_key] = 1
                else:
                    self.stacks[stack_key] += 1

    def step(self):
        self.current_step += 1

        for robot in self.robots:
            perception_json = self.get_perception(robot)
            action = robot.step(perception_json)
            self.update_environment(robot, action)

        if self.check_end_condition():
            self.stop()

    def check_end_condition(self):
        all_stacks_valid = all(1 <= stack_size <= 5 for stack_size in self.stacks.values())
        all_objects_stacked = sum(self.stacks.values()) == self.num_objects
        all_robots_believe_finished = all(not robot.onto_robot.is_holding for robot in self.robots)
        return all_stacks_valid and all_objects_stacked and all_robots_believe_finished

    def end(self):
        self.data['steps_to_completion'] = self.current_step
        print(f"Simulation ended after {self.data['steps_to_completion']} steps")
        print("Robot movements:")
        for robot_id, movements in self.data['robot_movements'].items():
            print(f"Robot {robot_id}: {movements} movements")

def run_model(parameters):
    model = ObjectStackingModel(parameters)
    results = model.run()
    return model, results

if __name__ == "__main__":
    parameters = {
        'num_objects': 20,
        'grid_size': 10
    }
    model, results = run_model(parameters)