from flask import Flask, request, jsonify
from Multiagent import MultiAgentSystem

app = Flask(__name__)
mas = MultiAgentSystem()

# Variable global para controlar la fase de la simulación
simulation_phase = "camera"

@app.route('/detect', methods=['POST'])
def detect():
    global simulation_phase
    data = request.json

    try:
        if simulation_phase == "camera":
            if 'Camera' not in data:
                return jsonify({"error": "Invalid data format for camera phase"}), 400
            
            camera_data = data['Camera']
            camera_results, drone_action, drone_direction = mas.process_detection(camera_data, None)
            
            # Chequeamos si alguna cámara detectó algo
            if any(result['action'] == 'alarm' for result in camera_results):
                simulation_phase = "drone"
            
            response = {
                "Camera": camera_results,
                "Drone": {
                    "action": drone_action,
                    "direction": drone_direction
                }
            }
        
        elif simulation_phase == "drone":
            if 'Drone' not in data:
                return jsonify({"error": "Invalid data format for drone phase"}), 400
            
            drone_data = data['Drone']
            camera_results, drone_action, drone_direction = mas.process_detection(None, drone_data)
            
            response = {
                "Drone": {
                    "action": drone_action,
                    "direction": drone_direction
                }
            }
        
        else:
            return jsonify({"error": "Invalid simulation phase"}), 500

        return jsonify(response)

    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)