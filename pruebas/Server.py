from flask import Flask, request, jsonify
from Multiagent import MultiAgentSystem
import logging
import json

app = Flask(__name__)
mas = MultiAgentSystem()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/detect', methods=['POST'])
def detect():
    data = request.json
    logger.info(f"Received data: {json.dumps(data, indent=2)}")
    logger.info(f"Current simulation phase: {mas.simulation_phase}")

    try:
        if mas.simulation_phase == "camera":
            if 'Camera' not in data:
                logger.error("Invalid data format for camera phase")
                return jsonify({"error": "Invalid data format for camera phase"}), 400
            
            camera_data = data['Camera']
            camera_results, drone_action = mas.process_detection(camera_data, None)
            
            response = {
                "Camera": camera_results,
                "Drone": drone_action
            }
        
        elif mas.simulation_phase in ["drone", "guard"]:
            if 'Drone' not in data:
                logger.error(f"Invalid data format for {mas.simulation_phase} phase")
                return jsonify({"error": f"Invalid data format for {mas.simulation_phase} phase"}), 400
            
            drone_data = data['Drone']
            _, action_result = mas.process_detection(None, drone_data)
            
            response = action_result
        
        else:
            logger.error(f"Invalid simulation phase: {mas.simulation_phase}")
            return jsonify({"error": "Invalid simulation phase"}), 500

        logger.info(f"Sending response: {json.dumps(response, indent=2)}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info("Starting server...")
    app.run(debug=True, port=5000)