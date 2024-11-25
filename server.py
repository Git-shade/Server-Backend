from flask import Flask, jsonify, request
from github2s import github2sCode

# Initialize the Flask app
app = Flask(__name__)

# Define the first route for a GET request
@app.route('/github2sRequest', methods=['GET'])
def github2s_request():

    # Extract parameters from the request body as JSON
    data = request.get_json()
    print(data)
    # Process the parameters using the github2sCode function
    result = github2sCode(data)
    
    # Return the result as a JSON response
    return jsonify({'result': result})

# Define the second route for a GET request
@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'Server is running'})

# Run the Flask server
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
