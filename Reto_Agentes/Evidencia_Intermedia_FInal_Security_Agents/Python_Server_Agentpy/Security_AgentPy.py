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
    
    #===================CAMERA ONTLOGY SECTION===================
    class Camera(Thing):
        pass

    class has_id(DataProperty, FunctionalProperty):
        domain = [Camera]
        range = [int] # Property acting as a variable to store the id of each camera instance.
        
    #===================DRON ONTLOGY SECTION===================
    class Dron(Thing):
        pass
     
    #===================SECURITY PERSONAL, CAMERA AND DRON ONTLOGY SECTION (PROPERTIES IN COMMON)===================
    class has_status(DataProperty, FunctionalProperty):
        domain = [Camera, Dron, Security_P]
        range = [str] # Status = "Normal" or "Detected".
        
    class has_action(DataProperty, FunctionalProperty):
        domain = [Camera, Dron, Security_P]
        range = [int] # Property acting as a variable to store the number of times that a Camera, Dron or the Security personal make an alert of an intruder.
    


# Save the ontology
onto.save()



class CamAgent(ap.Agent):
    def setup(self):
        self.onto_camera = onto.Camera(f"camera_{self.id}")  # Use the ID in the instance name
        self.onto_camera.has_status = "Normal"
        self.onto_camera.has_action = 0
        self.perception_data = {}
        self.rules = []
        
    def get_state(self):
        return {
            "id": self.onto_camera.has_id,
            "alert_sensor": self.onto_camera.has_status,
            "movements": self.onto_camera.has_action
        }
        
class DronAgent(ap.Agent):
    def setup(self):
        self.onto_Dron = onto.Dron(f"dron_{self.id}")  # Use the ID in the instance name
        self.onto_Dron.has_decision = "Normal"
        self.onto_Dron.has_action = 0
        self.perception_data = {}
        self.rules = []
        
    def get_state(self):
        return {
            "id": self.onto_Dron.has_id,
            "alert_sensor": self.onto_Dron.has_status,
            "movements": self.onto_Dron.has_action
        }
        
        
class SecurityAgent(ap.Agent):
    def setup(self):
        self.onto_Security_P = onto.Security_P(f"securityp_{self.id}")  # Use the ID in the instance name
        self.onto_Security_P.has_status = "Normal"
        self.onto_Security_P.has_decision = "Normal"
        self.onto_Security_P.has_action = 0
        self.perception_data = {}
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