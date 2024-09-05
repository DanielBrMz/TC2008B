import agentpy as ap
from owlready2 import *

# Create ontology
onto = get_ontology("http://example.org/camera_ontology.owl")

with onto:
    class Camera(Thing):
        pass
    
    class DetectedObject(Thing):
        pass
    
    class Fugitive(DetectedObject):
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
        domain = [Camera]
        range = [Position]
    
    class has_detected_object(FunctionalProperty, ObjectProperty):
        domain = [Camera]
        range = [DetectedObject]
    
    class has_action(FunctionalProperty, DataProperty):
        domain = [Camera]
        range = [str]

class CameraAgent(ap.Agent):
    def setup(self):
        self.camera = onto.Camera()
        self.camera_id = self.id  # Use the agent's id as camera_id
        print(f"CameraAgent {self.camera_id} setup completed")
    
    def detect(self, data):
        position = onto.Position()
        position.has_x = data['position'][0]
        position.has_y = data['position'][1]
        self.camera.has_position = position
        
        if data['Detect'] > 0:  # Any positive detection is treated as a Fugitive
            detected_object = onto.Fugitive()
            self.camera.has_detected_object = detected_object
            self.camera.has_action = "alarm"
        else:
            self.camera.has_detected_object = None
            self.camera.has_action = "ignore"
        
        return self.camera.has_action

class MultiAgentSystem:
    def __init__(self):
        self.model = ap.Model()
        self.setup()
        print("MultiAgentSystem initialized")

    def setup(self):
        self.camera_agents = {}
        for i in range(4):
            agent = CameraAgent(self.model)
            self.camera_agents[i] = agent
        print("MultiAgentSystem setup completed")
    
    def process_detection(self, data):
        print(f"Processing detection with data: {data}")
        results = []
        for camera_data in data:
            camera_id = camera_data['id']
            if camera_id in self.camera_agents:
                result = self.camera_agents[camera_id].detect(camera_data)
                results.append(result)
            else:
                print(f"Error: Camera agent with id {camera_id} not found")
                results.append("error")
        return results

def main():
    mas = MultiAgentSystem()
    # Add test code here if needed

if __name__ == "__main__":
    main()