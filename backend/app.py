from flask import Flask, request, jsonify
from routing_agent import RoutingAgent
from flask_cors import CORS
import tempfile
import os

app = Flask(__name__)

CORS(app, origins=["http://localhost:5173"])

agent = RoutingAgent()

@app.route("/submit-ticket", methods=["POST"])
def submit_ticket():
    user_message = request.form.get("message", "")
    pdf_file = request.files.get("pdf", None)
    saved_pdf_path = None
    if pdf_file:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_file.save(temp_file.name)
        saved_pdf_path = temp_file.name

    thread_id = request.form.get("thread_id", "default_thread")
    response = agent.handle_message(user_message, thread_id, pdf_path=saved_pdf_path)

    # Optionally delete temp file after processing
    if saved_pdf_path and os.path.exists(saved_pdf_path):
        os.remove(saved_pdf_path)

    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
