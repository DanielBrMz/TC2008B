from flask import Flask, request, jsonify, g
import json
import traceback
from RobotAgent import ObjectStackingModel, RobotAgent, onto

app = Flask(__name__)

def init_model_and_states():
    parameters = {
        'num_cams': 5,
        'num_dron': 1,
        'num_secper': 1,
    }
    model = SecurityDepartmentModel(parameters)
    model.setup()
    Cam_States = {cam.onto_camera.has_id: cam.get_state() for cam in model.cams}
    Dron_States = {dron.onto_Dron.has_id: dron.get_state() for dron in model.drons}
    Guard_States = {guard.onto_Security_P.has_id: guard.get_state() for guard in model.secguards}
    return model, Cam_States, Dron_States, Guard_States



@app.before_request
def before_request():
    if not hasattr(app, 'model') or not hasattr(app, 'Cam_States'):
        app.model, app.Cam_States, app.Dron_States, app.Guard_States  = init_model_and_states()
    app.logger.debug(f"Current cam states: {app.Cam_States}")
    app.logger.debug(f"Current dron states: {app.Dron_States}")
    app.logger.debug(f"Current guard states: {app.Guard_States}")


@app.route('/gmes', methods=['POST'])
def security_actions():
    try:
        data = request.json
        app.logger.debug(f"Received data: {data}")

        if not isinstance(data, dict):
            return jsonify({"error": "Invalid input. Expected a dictionary of security perceptions."}), 400

        actions = []
        
        if data["agent"] == "Camera":
            
            cameras = data["Cameras"]
            for cam_security_per in cameras:
                if 'id' not in cam_security_per or 'Detectpos' not in cam_security_per:
                    return jsonify({"error": "Invalid input. Each camera perception must have 'id' and 'Detectpos'."}), 400

                camera_id = cam_security_per['id']
                perception = cam_security_per['Detect']
                per_ubi = cam_security_per['Detectpos']
                
                if perception == 0:
                    continue

                camera_intance = next((r for r in app.model.cams if r.onto_camera.has_id == camera_id), None)
                if camera_intance is None:
                    app.logger.error(f"Camera with id {camera_id} not found.")
                    continue
                
                drons = data["Dron"]
                dron_security_per = drons[0]
                
                dron_id = dron_security_per['id']
                dron_intance = next((r for r in app.model.drons if r.onto_Dron.has_id == dron_id), None)
                if dron_intance is None:
                    app.logger.error(f"Dron with id {dron_id} not found.")
                    continue

                
                #======================================================
                #stored_state = app.robot_states.get(robot_id)
                #======================================================
                #app.logger.debug(f"Processing robot: {robot_id}, Stored state: {stored_state}")

                perception_json = json.dumps({
                    "id": camera_id,
                    "per": perception,
                    "per_ubi": per_ubi  
                })

                try:
                    camera_intance.step(perception_json)
                    action = dron_intance.step()
                    app.logger.debug(f"Action taken by Dron {dron_id}: {action}")
                    
                    action_parts = action.split('_')
                    action_type = action_parts[0]
                    direction = action_parts[1] if len(action_parts) > 1 else None

                    actions.append({
                        "Executor": "Dron",
                        "id": dron_id,
                        "action": action_type.capitalize()[0],
                        "direction": direction
                    })

                    #app.model.update_environment(robot, action)

                    app.Cam_States[camera_id] = camera_id.get_state()
                    app.logger.debug(f"Updated state for camera {camera_id}: {app.Cam_States[camera_id]}")
                    
                    app.Dron_States[dron_id] = dron_id.get_state()
                    app.logger.debug(f"Updated state for Dron {dron_id}: {app.Dron_States[dron_id]}")

                except Exception as e:
                    app.logger.error(f"Error in robot.step() for robot {camera_id}: {str(e)}")
                    app.logger.error(traceback.format_exc())
        
        elif data["agent"] == "Dron": 
            
            drons = data["Dron"]
            for dron_security_per in drons:
                if 'id' not in dron_security_per or 'Detect' not in dron_security_per:
                    return jsonify({"error": "Invalid input. Each dron perception must have 'id' and 'Detectpos'."}), 400

                dron_id = dron_security_per['id']
                perception = dron_security_per['Detect']
                dron_ubi = dron_security_per['ubi']

                dron_intance = next((r for r in app.model.drons if r.onto_Dron.has_id == dron_id), None)
                if dron_intance is None:
                    app.logger.error(f"Dron with id {dron_id} not found.")
                    continue

                
                #======================================================
                stored_state = app.Dron_States.get(dron_id)
                #======================================================
                
                app.logger.debug(f"Processing Dron: {dron_id}, Stored state: {stored_state}")

                perception_json = json.dumps({
                    "id": dron_id,
                    "per": perception,
                    "dron_ubi": dron_ubi  
                })

                try:
                    action = dron_intance.step(perception_json, stored_state)
                    app.logger.debug(f"Action taken by Dron {dron_id}: {action}")
                    
                    app.Dron_States[dron_id] = dron_id.get_state()
                    app.logger.debug(f"Updated state for Dron {dron_id}: {app.Dron_States[dron_id]}")
                    
                    stored_state = app.Dron_States.get(dron_id)
                    if stored_state["perception"] in {1, 2}:
                        # HEREEEEEEEE: In this section of the code, we can add a conditional statement to handle the case where the Dron finally detects something using computer vision. 
                        # There are two valid values that indicate the Dron has detected something: 1 or 2, which are part of the perception data. When either of these values 
                        # is detected, the system will trigger the step method of the Guard agent.
                        # IMPORTANT: If we use this logic maybe we need that the computational vision of the dron manage the 0 cases. Like until the drone reach or see some animal or 
                        # person needs to send by the post method from the client the perception of 0(APPARENTLY NOTHING IN THE VIEW).
                        return 0
                    
                    action_parts = action.split('_')
                    action_type = action_parts[0]
                    direction = action_parts[1] if len(action_parts) > 1 else None

                    actions.append({
                        "Executor": "Dron",
                        "id": dron_id,
                        "action": action_type.capitalize()[0],
                        "direction": direction
                    })

                    #app.model.update_environment(robot, action)

                    
                    
                except Exception as e:
                    app.logger.error(f"Error in robot.step() for robot {camera_id}: {str(e)}")
                    app.logger.error(traceback.format_exc())          
                    
        app.model.current_step += 1

        if app.model.check_end_condition():
            app.logger.info("Simulation ended")
            app.model.end()

        app.logger.debug(f"Final robot states after this step: {app.robot_states}")
        return jsonify(actions[-1])
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "An internal server error occurred", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)