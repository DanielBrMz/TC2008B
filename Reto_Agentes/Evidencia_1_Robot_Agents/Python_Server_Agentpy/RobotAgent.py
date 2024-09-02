import agentpy as ap
import json
import random
from owlready2 import *

# Create the ontology
onto = get_ontology("file://onto.owl")

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

    class has_position(ObjectProperty):
        domain = [Robot]
        range = [Position]

    class is_holding(ObjectProperty):
        domain = [Robot]
        range = [Object]

    class has_perception(ObjectProperty):
        domain = [Robot]
        range = [Direction]

    class can_perform(ObjectProperty):
        domain = [Robot]
        range = [Action]

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
        self.perception_data = {}
        self.is_holding_box = False
        self.rules = [
            ({"perception": {"F": 1}, "is_holding": False}, "grab_F"),
            ({"perception": {"B": 1}, "is_holding": False}, "grab_B"),
            ({"perception": {"L": 1}, "is_holding": False}, "grab_L"),
            ({"perception": {"R": 1}, "is_holding": False}, "grab_R"),
            ({"perception": {"F": 3}, "is_holding": True}, "drop_F"),
            ({"perception": {"B": 3}, "is_holding": True}, "drop_B"),
            ({"perception": {"L": 3}, "is_holding": True}, "drop_L"),
            ({"perception": {"R": 3}, "is_holding": True}, "drop_R"),
        ]

    def get_state(self):
        return {
            "id": self.onto_robot.id,
            "is_holding_box": self.is_holding_box,
            "movements": self.movements
        }

    #POR QUE STORED_STATE ESTA SETEADO COMO NONE?
    def update_state(self, perception_json, stored_state=None):
        print(f"Updating state with perception: {perception_json}")
        perception = json.loads(perception_json)
        self.onto_robot.id = perception["id"]
        self.perception_data = perception["position"]
        if stored_state:
            #self.is_holding_box = stored_state["is_holding_box"]
            self.movements = stored_state["movements"]
        print(f"State updated. Robot ID: {self.onto_robot.id}, Holding: {self.is_holding_box}, Perception: {self.perception_data}")

    def check_rule(self, rule):
        for key, value in rule.items():
            if key == "perception":
                for direction, expected in value.items():
                    if self.perception_data.get(direction) != expected:
                        return False
            elif key == "is_holding":
                if self.is_holding_box != value:
                    return False
        return True

    def get_box_directions(self):
        return [direction for direction, value in self.perception_data.items() if value == 1]

    def get_stack_directions(self):
        return [direction for direction, value in self.perception_data.items() if value == 3]

    def get_free_directions(self):
        return [direction for direction, value in self.perception_data.items() if value == 0]

    def perceive_and_act(self):
        print(f"Perceiving and acting. Is holding box: {self.is_holding_box}")
        
        if self.is_holding_box:
            stack_directions = self.get_stack_directions()
            if stack_directions:
                chosen_direction = random.choice(stack_directions)
                print(f"Found stack. Dropping box in direction: {chosen_direction}")
                return f"drop_{chosen_direction}"
            else:
                free_directions = self.get_free_directions()
                if free_directions:
                    chosen_direction = random.choice(free_directions)
                    print(f"Holding box, moving to free space: {chosen_direction}")
                    return f"move_{chosen_direction}"
                else:
                    print("No free space, staying put")
                    return "wait"
        else:
            box_directions = self.get_box_directions()
            if box_directions:
                chosen_direction = random.choice(box_directions)
                print(f"Found box. Grabbing from direction: {chosen_direction}")
                return f"grab_{chosen_direction}"

        free_directions = self.get_free_directions()
        if free_directions:
            chosen_direction = random.choice(free_directions)
            print(f"Moving to free space: {chosen_direction}")
            return f"move_{chosen_direction}"
        else:
            print("No free space, staying put")
            return "wait"
        
    def act(self, action):
        print(f"Acting: {action}")
        if action.startswith("move_"):
            self.movements += 1
        elif action.startswith("grab_"):
            self.is_holding_box = True
        elif action.startswith("drop_"):
            self.is_holding_box = False
        return action

    def reason(self):
        print("Reasoning about action")
        action = self.perceive_and_act()
        return json.dumps({"action": action})

    def step(self, perception_json, stored_state=None):
        print(f"Step method called with perception: {perception_json}")
        self.update_state(perception_json, stored_state)
        action = self.perceive_and_act()
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
            robot.onto_robot.id = i
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
                cell_content = self.grid.agents[new_x, new_y]  # Changed this line
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