# Server.py
from flask import Flask, request, jsonify
from Multiagent import MultiAgentSystem
import logging
import json

app = Flask(__name__)
mas = MultiAgentSystem()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variable to control the simulation phase
simulation_phase = "camera"

@app.route('/detect', methods=['POST'])
def detect():
    global simulation_phase
    data = request.json

    logger.info(f"Received data: {json.dumps(data, indent=2)}")
    logger.info(f"Current simulation phase: {simulation_phase}")

    try:
        if simulation_phase == "camera":
            if 'Camera' not in data:
                logger.error("Invalid data format for camera phase")
                return jsonify({"error": "Invalid data format for camera phase"}), 400
            
            camera_data = data['Camera']
            logger.info(f"Processing camera data: {json.dumps(camera_data, indent=2)}")
            camera_results, drone_action, drone_direction = mas.process_detection(camera_data, None)
            
            # Check if any camera detected something
            if any(result['action'] == 'alarm' for result in camera_results):
                simulation_phase = "drone"
                logger.info("Switching to drone phase")
            
            response = {
                "Camera": camera_results,
                "Drone": {
                    "action": drone_action,
                    "direction": drone_direction
                }
            }
        
        elif simulation_phase == "drone":
            if 'Drone' not in data:
                logger.error("Invalid data format for drone phase")
                return jsonify({"error": "Invalid data format for drone phase"}), 400
            
            drone_data = data['Drone']
            logger.info(f"Processing drone data: {json.dumps(drone_data, indent=2)}")
            camera_results, drone_action, drone_direction = mas.process_detection(None, drone_data)
            
            response = {
                "Drone": {
                    "action": drone_action,
                    "direction": drone_direction
                }
            }
        
        else:
            logger.error(f"Invalid simulation phase: {simulation_phase}")
            return jsonify({"error": "Invalid simulation phase"}), 500

        logger.info(f"Sending response: {json.dumps(response, indent=2)}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    logger.error(f"404 error: {str(error)}")
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    logger.info("Starting server...")
    app.run(debug=True, port=5000)