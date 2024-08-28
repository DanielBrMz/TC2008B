from flask import Flask, request, jsonify
import agentpy as ap
import json
import traceback
from RobotAgent import ObjectStackingModel, RobotAgent, onto

app = Flask(__name__)

# Initialize the model
parameters = {
    'num_objects': 20,
    'grid_size': 10,
}
model = ObjectStackingModel(parameters)
model.setup()

@app.route('/gmrs', methods=['POST'])
def robot_action():
    try:
        data = request.json
        
        app.logger.debug(f"Received data: {data}")
        app.logger.debug(f"Ontology classes: {list(onto.classes())}")
        app.logger.debug(f"Ontology individuals: {list(onto.individuals())}")

        if not data or 'id' not in data or 'position' not in data:
            return jsonify({"error": "Invalid input"}), 400

        robot_id = data['id']
        perception = data['position']

        app.logger.debug(f"Current robots in model: {[r.onto_robot.id for r in model.robots]}")

        robot = next((r for r in model.robots if r.onto_robot.id == robot_id), None)
        if robot is None:
            app.logger.error(f"Robot with id {robot_id} not found.")
            return jsonify({"error": "Robot not found"}), 404

        app.logger.debug(f"Found robot: {robot.onto_robot.id}, Position: {robot.onto_robot.has_position}")

        perception_json = json.dumps({
            "id": robot_id,
            "position": perception
        })

        app.logger.debug(f"Perception JSON: {perception_json}")

        try:
            action = robot.step(perception_json)
            app.logger.debug(f"Action taken by robot: {action}")
        except Exception as e:
            app.logger.error(f"Error in robot.step(): {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({"error": f"Error in robot action: {str(e)}"}), 500

        try:
            model.update_environment(robot, action)
        except Exception as e:
            app.logger.error(f"Error in model.update_environment(): {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({"error": f"Error updating environment: {str(e)}"}), 500

        action_parts = action.split('_')
        action_type = action_parts[0]
        direction = action_parts[1] if len(action_parts) > 1 else None

        response = {
            "action": action_type,
            "direction": direction
        }

        return jsonify(response)

    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "An internal server error occurred", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)