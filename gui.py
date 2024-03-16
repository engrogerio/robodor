from flask import Flask, render_template, request, jsonify
import json


app = Flask(__name__)

# File to store JSON data
json_file = "tasks.json"

def load_json_data():
    with open(json_file, "r") as file:
        data = [json.loads(line.strip()) for line in file if line.strip()]
    return data

def save_json_data(data):
    with open(json_file, "w") as file:
        for item in data:
            file.write(json.dumps(item) + '\n')

@app.route('/diario')
def index():
    task_data = load_json_data()
    print('*****', task_data)
    return render_template('index.html', data={"items": task_data})

@app.route('/diario/atualiza', methods=['POST'])
def update_data():
    # Receive the updated JSON data from the form
    updated_data = request.json
    # Update the JSON file data with the received data
    update_json_file(updated_data)
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
