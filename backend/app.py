from flask import Flask, request, jsonify
from routing_agent import RoutingAgent
from flask_cors import CORS

app = Flask(__name__)

CORS(app, origins=["http://localhost:5173"])

agent = RoutingAgent()

@app.route('/submit-ticket', methods=['POST'])
def submit_ticket():
    data = request.json
    thread_id = data.get('thread_id', 'default_thread')  # get or create a thread_id
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Pass message and thread_id to agent for processing with memory
    response = agent.handle_message(user_message, thread_id)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
