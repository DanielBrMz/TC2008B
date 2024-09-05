import agentpy as ap
import json
import random
from owlready2 import *

# Create the ontology
onto = get_ontology("file://onto.owl")

with onto:
    #===================SECURITY PERSON ONTLOGY SECTION===================
    class Security_P(Thing):
        pass
    
    class has_decision(DataProperty, FunctionalProperty):
        domain = [Security_P]
        range = [str] # Property acting as the decision of the security person. 
        # Status = "Normal" or "Alert".
        
    #===================DRON ONTLOGY SECTION===================
    class Dron(Thing):
        pass
    
    class has_ubi(DataProperty, FunctionalProperty):
        domain = [Dron, Security_P]
        range = [str] # Property acting as a variable to store the initial location of the Dron.
    
    #===================CAMERA ONTLOGY SECTION===================
    class Camera(Thing):
        pass

    class has_id(DataProperty, FunctionalProperty):
        domain = [Camera, Dron, Security_P]
        range = [int] # Property acting as a variable to store the id of each Camera, Dron or the Security personal instance.
     
    #===================SECURITY PERSONAL, CAMERA AND DRON ONTLOGY SECTION (PROPERTIES IN COMMON)===================
    class has_status(DataProperty, FunctionalProperty):
        domain = [Camera, Dron, Security_P]
        range = [str] # Status = "Normal" or "Detected".
        
    class has_action(DataProperty, FunctionalProperty):
        domain = [Camera, Dron, Security_P]
        range = [int] # Property acting as a variable to store the number of times that a Camera, Dron or the Security personal make an alert of an intruder.
        
    class has_perception(DataProperty, FunctionalProperty):
        domain = [Camera, Dron, Security_P]
        range = [int] # Property acting as a variable to store what the Camera, Dron or the Security personal are seeing. 0, 1 or 2.
        
    class has_per_ubi(DataProperty, FunctionalProperty):
        domain = [Camera, Dron, Security_P]
        range = [str] # Property acting as a variable to store the location of the sospicious game object.
        
    
    


# Save the ontology
onto.save()



class MessagesSharedResource:
    def __init__(self):
        self.perception = None
        self.per_ubi = None  

class CamAgent(ap.Agent):
    def setup(self):
        self.shared_resource = self.model.shared_resource
        self.onto_camera = onto.Camera(f"camera_{self.id}")  # Use the ID in the instance name
        self.onto_camera.has_status = "Normal"
        self.onto_camera.has_action = 0
        #self.perception_data = {}
        self.rules = []
        
    def get_state(self):
        return {
            "id": self.onto_camera.has_id,
            "alert_sensor": self.onto_camera.has_status,
            "movements": self.onto_camera.has_action
        }
        
    #def perceive_and_act(self):
    #    print(f"Perceiving and acting camera.")
        
        
    def update_state(self, perception_json):
        print(f"Updating state with perception: {perception_json}")
        perception = json.loads(perception_json)
        self.onto_camera.has_perception = perception["per"]
        self.onto_camera.has_per_ubi = perception["per_ubi"]
        self.onto_camera.has_action += 1 
        self.onto_camera.has_status = "Detected" 
        self.shared_resource.perception = self.onto_camera.has_perception
        self.shared_resource.per_ubi = self.onto_camera.has_per_ubi
        
        
        print(f"State updated. Camera ID: {self.onto_camera.has_id}, Seeing: {self.onto_camera.has_perception}, In a distance from the Dron: {self.onto_camera.has_per_ubi}")
        
    def step(self, perception_json):
        print(f"Step method called with perception: {perception_json}")
        self.update_state(perception_json)
        

class DronAgent(ap.Agent):
    def setup(self):
        self.onto_Dron = onto.Dron(f"dron_{self.id}")  # Use the ID in the instance name
        self.onto_Dron.has_decision = "Normal"
        self.onto_Dron.has_action = 0
        self.onto_Dron.has_ubi = "(0, 0)" #Initial location fo the Dron
        #self.perception_data = {}
        self.rules = []
        
    def get_state(self):
        return {
            "id": self.onto_Dron.has_id,
            "perception": self.onto_Dron.has_perception,
            "perceptionUbi": self.onto_Dron.has_per_ubi
        }
        
    def perceive_and_act():
        # Logic to perform the action that the dron needs to return to the client.
        # This action must be performed with the values stored in the ontology: has_perception, has_perception_ubi and has_ubi.
        # has_perception : The thing that the Camera or Dron is seeing. 0: NOTHING(ERROR CONTROL) || 1: ANIMAL / THING  || 2: PRISIONER.
        # has_per_ubi : The distance between the suspicious thing and the Dron.
        return 0
    
    def update_state(self, perception_json = None):
        if self.onto_Dron.has_action == 0 and perception_json is None :
            print("Receiving information from Camera Agent.")
            self.onto_Dron.has_perception = self.shared_resource.perception 
            self.onto_Dron.has_per_ubi = self.shared_resource.per_ubi 
        else:
            print(f"Updating state with perception: {perception_json}")
            perception = json.loads(perception_json)
            self.onto_Dron.has_perception = perception["per"]
            self.onto_Dron.has_per_ubi = perception["per_ubi"]
            
        self.onto_Dron.has_action += 1 
        
        print(f"State updated. Dron ID: {self.onto_Dron.has_id}, Seeing: {self.onto_Dron.has_perception}, In a distance from the Dron: {self.onto_Dron.has_per_ubi}")
        
    def step(self, perception_json = None):
        print(f"Step method called with perception: {perception_json}")
        self.update_state(perception_json)                                                                                                                                                                            
        action = self.perceive_and_act()
        return self.act(action)
        
class SecurityAgent(ap.Agent):
    def setup(self):
        self.onto_Security_P = onto.Security_P(f"securityp_{self.id}")  # Use the ID in the instance name
        self.onto_Security_P.has_status = "Normal"
        self.onto_Security_P.has_decision = "Normal"
        self.onto_Security_P.has_action = 0
        #self.perception_data = {}
        self.rules = []
        
    def get_state(self):
        return {
            "id": self.onto_Security_P.has_id,
            "alert_sensor": self.onto_Security_P.has_status,
            "alert_decision": self.onto_Security_P.has_decision,
            "movements": self.onto_Security_P.has_action
        }
        



class SecurityDepartmentModel(ap.Model):
    def setup(self):
        self.shared_resource = MessagesSharedResource()
        self.num_cams = self.p.num_cams
        self.num_dron = self.p.num_dron
        self.num_securityper = self.p.num_secper
        self.current_step = 0

        self.cams = ap.AgentList(self, self.num_cams, CamAgent)
        self.drons = ap.AgentList(self, self.num_dron, DronAgent)
        self.secguards = ap.AgentList(self, self.num_securityper, SecurityAgent)
        
        
        for i, cam in enumerate(self.cams):
            cam.id = i  # Assign the unique ID
            cam.onto_camera.has_id = i  # Update the ontology with the correct ID
            
        for i, dron in enumerate(self.drons):
            dron.id = i  # Assign the unique ID
            dron.onto_Dron.has_id = i  # Update the ontology with the correct ID
            
        for i, guard in enumerate(self.secguards):
            guard.id = i  # Assign the unique ID
            guard.onto_Security_P.has_id = i  # Update the ontology with the correct ID
            
            
        #self.data = {
        #    'steps_to_completion': None,
        #    'robot_movements': {cam.onto_camera.id: 0 for robot in self.robots}
        #}