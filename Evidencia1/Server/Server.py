from flask import Flask, request, jsonify
import agentpy as ap
import json
from RobotAgent import ObjectStackingModel, Robot

app = Flask(__name__)

# Initialize the model
parameters = {
    'num_objects': 20,
    'grid_size': 10,
}
model = ObjectStackingModel(parameters)
model.setup()

@app.route('/gmrs', methods=['POST'])

@app.route('/gmrs', methods=['POST'])
def robot_action():
    try:
        data = request.json
        
        # Log the received data for debugging
        app.logger.debug(f"Received data: {data}")

        if not data or 'id' not in data or 'position' not in data:
            return jsonify({"error": "Invalid input"}), 400

        robot_id = data['id']
        perception = data['position']

        # Log robot list to check if robots are initialized correctly
        app.logger.debug(f"Current robots in model: {[r.onto_robot.id for r in model.robots]}")

        # Find the correct robot using onto_robot.id
        robot = next((r for r in model.robots if r.onto_robot.id == robot_id), None)
        if robot is None:
            app.logger.error(f"Robot with id {robot_id} not found.")
            return jsonify({"error": "Robot not found"}), 404

        # Log robot's current state
        app.logger.debug(f"Found robot: {robot.onto_robot.id}, Position: {robot.onto_robot.has_position}")

        # Create the perception JSON
        perception_json = json.dumps({
            "id": robot_id,
            "position": perception
        })

        # Log perception JSON
        app.logger.debug(f"Perception JSON: {perception_json}")

        # Get the robot's action
        action = robot.step(perception_json)

        # Log the action to debug
        app.logger.debug(f"Action taken by robot: {action}")

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