from flask import Flask, request, jsonify
from Multiagent import MultiAgentSystem

app = Flask(__name__)
mas = MultiAgentSystem()

@app.route('/detect', methods=['POST'])
def detect():
    data = request.json
    camera_data = data['Camera']
    
    # Process data with the multi-agent system
    results = mas.process_detection(camera_data)
    
    response = {
        "Camera": [
            {
                "id": camera["id"],
                "action": result
            } for camera, result in zip(camera_data, results)
        ]
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)