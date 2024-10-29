from flask import Flask, request, jsonify
from flask_cors import CORS
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

import os
import requests
import logging

load_dotenv()

app = Flask(__name__)
CORS(app)

# Twilio credentials
account_sid = os.getenv('ACCOUNT_SID')
auth_token = os.getenv('AUTH_TOKEN')
workspace_sid = os.getenv('TWILIO_WORKSPACE_SID')

# Load the Numverify API key from environment variables
NUMVERIFY_API_KEY = os.getenv('NUMVERIFY_API_KEY')
NUMVERIFY_API_URL = 'https://api.apilayer.com/number_verification/validate'

# Enable logging
logging.basicConfig(level=logging.INFO)

client = Client(account_sid, auth_token)

@app.route('/api')
def hello():
    return "Hello, Twilio Plugin!"


# Function to fetch friendly name of a phone number
def fetch_friendly_name(phone_number):
    numbers = client.incoming_phone_numbers.list()
    for record in numbers:
        if record.phone_number == phone_number:
            return record.friendly_name
    return "Unknown phone number" # Return number if no friendly name found

# Endpoint to get the location and friendly name based on the phone number
@app.route('/api/call-location-name/<phone_number>', methods=['GET'])
def call_location(phone_number):
    try:
        # Call Numverify API to get country and location data
        params = {
            'access_key': NUMVERIFY_API_KEY,
            'number': phone_number,
        }
        response = requests.get(NUMVERIFY_API_URL, params=params)
        data = response.json()

        if response.status_code == 200 and data['valid']:
            # Get friendly name from the phone number
            friendly_name = fetch_friendly_name(phone_number)
            # Extract country name from the response
            country_name = data.get('country_name', 'Unknown Location')
            return jsonify({'location': country_name, 'friendly_name': friendly_name}), 200
        else:
            return jsonify({'location': 'Unknown Location', 'friendly_name': friendly_name}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        

# Endpoint to fetch call history
@app.route('/api/call-logs', methods=['GET'])
def get_call_logs():
    try:
        calls = client.calls.list(limit=50)  # Fetch the last 50 calls

        call_logs = [
            {
                'from': call._from,
                'to': call.to,
                'status': call.status,
                'duration': call.duration,
                'start_time': str(call.start_time),
            }
            for call in calls
        ]

        return jsonify(call_logs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to fetch task history
@app.route('/api/task-logs', methods=['GET'])
def get_task_logs():
    try:
        # Fetch the last 50 tasks from TaskRouter
        tasks = client.taskrouter.workspaces(workspace_sid).tasks.list(limit=50)

        task_logs = [
            {
                'sid': task.sid,
                'status': task.assignment_status,
                'created_time': str(task.date_created),
                'attributes': task.attributes,
            }
            for task in tasks
        ]

        return jsonify(task_logs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Fetch past SMS messages
@app.route('/api/sms-logs', methods=['GET'])
def fetch_sms_history():
    try:
        messages = client.messages.list(limit=20)
        sms_logs = [{
            "message_sid": message.sid,
            "body": message.body,
            "from": message.from_,
            "to": message.to,
            "status": message.status,
            "date_sent": message.date_sent
        } for message in messages]
        return jsonify(sms_logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Send SMS messages
@app.route('/api/send-sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    to = data.get('to')  # The recipient's phone number
    body = data.get('body')  # The message body
    from_ = data.get('from')  # The sender's phone number (Twilio number)

    # Validate input
    if not to or not body:
        return jsonify({'error': 'Recipient phone number and message body are required.'}), 400

    # Validate the 'from' number
    if from_:
        try:
            # Check if the 'from' number is a valid Twilio number
            incoming_numbers = client.incoming_phone_numbers.list()
            valid_numbers = [number.phone_number for number in incoming_numbers]
            if from_ not in valid_numbers:
                return jsonify({'error': 'The provided "from" number is not a valid Twilio number.'}), 400
            message = client.messages.create(body=body, from_=from_, to=to)
            return jsonify({'message_sid': message.sid, 'status': 'sent'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': '"from" number is required.'}), 400

    try:
        # Send the SMS
        message = client.messages.create(
            body=body,
            from_=from_,
            to=to
        )
        return jsonify({'message_sid': message.sid, 'status': 'sent'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# Webhook to receive incoming SMS
@app.route('/api/receive-sms', methods=['POST'])
def receive_sms():
    try:
        # Validate incoming request data
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        message_body = request.form.get('Body')        

        # Check if necessary fields are present
        if not from_number or not to_number or not message_body:
            logging.error("Invalid data in request: missing From, To, or Body.")
            return jsonify({
                "status": "error",
                "message": "Invalid request. 'From', 'To', and 'Body' fields are required."
            }), 400

        # Log the incoming SMS details
        logging.info(f"Received SMS from {from_number} to {to_number}: {message_body}")

        # Handle the incoming message based on the Twilio number (To)
        # Check if the 'to' number is a valid Twilio number
        incoming_numbers = client.incoming_phone_numbers.list()
        valid_numbers = [number.phone_number for number in incoming_numbers]
        if to_number in valid_numbers:
            logging.info(f"Handling message for {to_number} from {from_number}: {message_body}")
            response_message = f"Hello, your message '{message_body[:20]}...' was received by our service number {to_number}"
        else:
            # Handle unrecognized Twilio number
            logging.warning(f"Unrecognized Twilio number: {to_number}")
            response_message = "Sorry, we couldn't process your message."
        
            

        # Prepare the Twilio response (SMS reply)
        twilio_response = MessagingResponse()
        twilio_response.message(response_message)

        # Send a successful response to the client
        return str(twilio_response), 200

    except Exception as e:
        logging.error(f"Error processing SMS: {e}")
        return jsonify({
            "status": "error",
            "message": "An internal error occurred while processing the SMS."
        }), 500

@app.route('/api/agent-status', methods=['POST'])
def update_agent_status():
    data = request.get_json()
    worker_sid = data.get("worker_sid")
    activity_sid = data.get("activity_sid")  # Activity SID for 'Online' status

    if not worker_sid or not activity_sid:
        return jsonify({"error": "worker_sid and activity_sid are required"}), 400

    try:
        worker = client.taskrouter.workspaces(workspace_sid) \
                    .workers(worker_sid) \
                    .update(activity_sid=activity_sid)
        return jsonify({
            "worker_sid": worker_sid,
            "status": "online"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/allow-multiple-agents', methods=['POST'])
def allow_multiple_agents():
    data = request.get_json()
    task_sid = data.get("task_sid")

    if not task_sid:
        return jsonify({"error": "task_sid is required"}), 400

    try:
        task = client.taskrouter.workspaces(workspace_sid) \
                    .tasks(task_sid) \
                    .update(assignment_status='pending')
        return jsonify({
            "task_sid": task_sid,
            "status": "pending"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/answer-call', methods=['POST'])
def answer_call():
    data = request.get_json()
    call_sid = data.get("call_sid")
    worker_sid = data.get("worker_sid")

    if not call_sid or not worker_sid:
        return jsonify({"error": "call_sid and worker_sid are required"}), 400

    try:
        call = client.calls(call_sid).update(status='in-progress')  # Set call status to "in-progress" to answer
        return jsonify({
            "call_sid": call_sid,
            "status": "answered"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/update-call-history', methods=['POST'])
def update_call_history():
    data = request.get_json()
    call_sid = data.get("call_sid")
    call_details = {
        "from": data.get("from"),
        "to": data.get("to"),
        "status": data.get("status"),
        "duration": data.get("duration"),
        "start_time": data.get("start_time")
    }

    # Check if essential fields are provided
    if not call_sid or not call_details["from"] or not call_details["to"]:
        return jsonify({"error": "call_sid, from, and to are required"}), 400

    try:
        return jsonify({
            "status": "call history updated",
            "call_sid": call_sid
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
    