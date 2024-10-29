## The Backend for A custom twilio plugin

Below is a structured outline of the expected requests and responses for each API endpoint based on your Flask backend implementation:

---

### **1. `GET /api`**
   - **Description**: Basic endpoint to confirm API availability.
   - **Response**:
      ```json
      "Hello, Twilio Plugin!"
      ```

---

### **2. `GET /api/call-location-name/<phone_number>`**
   - **Description**: Retrieves the location and friendly name for a specific phone number using Numverify and Twilio APIs.
   - **Request Parameters**:
      - `phone_number` (URL parameter): The phone number for which location and friendly name are requested.
   - **Response**:
      - **Success (200)**:
         ```json
         {
            "location": "Country Name",
            "friendly_name": "Friendly Name"
         }
         ```
      - **Error (400)**: Invalid phone number.
         ```json
         {
            "location": "Unknown Location",
            "friendly_name": "Unknown phone number"
         }
         ```
      - **Error (500)**: Server error with exception details.
         ```json
         {
            "error": "Error details"
         }
         ```

---

### **3. `GET /api/call-logs`**
   - **Description**: Fetches the last 50 call logs.
   - **Response**:
      - **Success (200)**:
         ```json
         [
            {
               "from": "+1234567890",
               "to": "+0987654321",
               "status": "completed",
               "duration": "60",
               "start_time": "2024-10-27T12:00:00Z"
            },
            ...
         ]
         ```
      - **Error (500)**: Server error with exception details.
         ```json
         {
            "error": "Error details"
         }
         ```

---

### **4. `GET /api/task-logs`**
   - **Description**: Fetches the last 50 tasks from TaskRouter.
   - **Response**:
      - **Success (200)**:
         ```json
         [
            {
               "sid": "task_sid",
               "status": "completed",
               "created_time": "2024-10-27T12:00:00Z",
               "attributes": "Task attributes as string or JSON"
            },
            ...
         ]
         ```
      - **Error (500)**: Server error with exception details.
         ```json
         {
            "error": "Error details"
         }
         ```

---

### **5. `GET /api/sms-logs`**
   - **Description**: Fetches the last 20 SMS logs.
   - **Response**:
      - **Success (200)**:
         ```json
         [
            {
               "message_sid": "sms_sid",
               "body": "Hello there!",
               "from": "+1234567890",
               "to": "+0987654321",
               "status": "delivered",
               "date_sent": "2024-10-27T12:00:00Z"
            },
            ...
         ]
         ```
      - **Error (500)**: Server error with exception details.
         ```json
         {
            "error": "Error details"
         }
         ```

---

### **6. `POST /api/send-sms`**
   - **Description**: Sends an SMS message.
   - **Request Body**:
      ```json
      {
         "to": "+0987654321",
         "from": "+1234567890",
         "body": "Hello there!"
      }
      ```
   - **Response**:
      - **Success (200)**:
         ```json
         {
            "message_sid": "sms_sid",
            "status": "sent"
         }
         ```
      - **Error (400)**: Missing required fields or invalid `from` number.
         ```json
         {
            "error": "Error message"
         }
         ```
      - **Error (500)**: Server error with exception details.
         ```json
         {
            "error": "Error details"
         }
         ```

---

### **7. `POST /api/receive-sms`**
   - **Description**: Webhook endpoint for receiving incoming SMS messages.
   - **Request Parameters** (Form Data):
      - `From`: The sender’s phone number.
      - `To`: The Twilio number that received the message.
      - `Body`: The text body of the message.
   - **Response**:
      - **Success (200)**: Twilio Messaging Response XML with acknowledgment message.
         ```xml
         <Response>
            <Message>Hello, your message 'Hello...' was received by our service number +1234567890</Message>
         </Response>
         ```
      - **Error (400)**: Missing required fields.
         ```json
         {
            "status": "error",
            "message": "Invalid request. 'From', 'To', and 'Body' fields are required."
         }
         ```
      - **Error (500)**: Server error with exception details.
         ```json
         {
            "status": "error",
            "message": "An internal error occurred while processing the SMS."
         }
         ```

