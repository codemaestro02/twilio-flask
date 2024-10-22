from flask import Flask, request, jsonify
from flask_cors import CORS
from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

# Twilio credentials
account_sid = os.getenv('ACCOUNT_SID')
auth_token = os.getenv('AUTH_TOKEN')
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
    return phone_number  # Return number if no friendly name found

@app.route('/api/friendly-name/<phone_number>', methods=['GET'])
def get_friendly_name(phone_number):
    friendly_name = fetch_friendly_name(phone_number)
    return jsonify({'friendly_name': friendly_name})

# Fetch recent call logs
@app.route('/api/call-logs', methods=['GET'])
def fetch_past_calls():
    calls = client.calls.list(limit=20)
    call_logs = [{
        "call_sid": call.sid,
        "to": call.to,
        "from": call._from,
        "dateCreated": call.date_created,
        "duration": call.duration,
        "start_time": call.start_time
    } for call in calls]
    return jsonify(call_logs)

# Fetch past SMS messages
@app.route('/api/sms-logs', methods=['GET'])
def fetch_sms_chats():
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

# Update agent's status after a missed call
def configure_agent_online(worker_sid):
    worker = client.taskrouter.workspaces('your_workspace_sid') \
                .workers(worker_sid) \
                .update(activity_sid='online_activity_sid')
    return worker

# Allow multiple agents for a task
def allow_multiple_agents(task_sid):
    task = client.taskrouter.workspaces('your_workspace_sid') \
                .tasks(task_sid) \
                .update(assignment_status='pending')
    return task

if __name__ == '__main__':
    app.run(debug=True)
    