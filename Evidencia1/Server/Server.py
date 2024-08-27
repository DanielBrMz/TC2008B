from flask import Flask, request, jsonify
import agentpy as ap
import json
from RobotAgent import ObjectStackingModel, Robot

app = Flask(__name__)

# Initialize the model
parameters = {
    'num_objects': 20,
    'grid_size': 10,
    'max_steps': 1000
}
model = ObjectStackingModel(parameters)
model.setup()

@app.route('/gmrs', methods=['POST'])

def robot_action():
    try:
        data = request.json
        
        if not data or 'id' not in data or 'position' not in data:
            return jsonify({"error": "Invalid input"}), 400

        robot_id = data['id']
        perception = data['position']

        # Find the correct robot
        robot = next((r for r in model.robots if r.id == robot_id), None)
        if robot is None:
            return jsonify({"error": "Robot not found"}), 404

        # Create the perception JSON
        perception_json = json.dumps({
            "id": robot_id,
            "position": perception
        })

        # Get the robot's action
        action = robot.step(perception_json)

        # Update the model's environment
        model.update_environment(robot, action)

        # Parse the action
        action_parts = action.split('_')
        action_type = action_parts[0]
        direction = action_parts[1] if len(action_parts) > 1 else None

        # Prepare the response
        response = {
            "action": action_type,
            "direction": direction
        }

        return jsonify(response)

    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        return jsonify({"error": "An internal server error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True)