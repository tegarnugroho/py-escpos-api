# py-escpos-api
Sure! Here's the updated version with an opening sentence and mentioning that the project uses `app.py`:

To run the application and access the API endpoints on your Raspberry Pi, follow these steps:

1. **Install required dependencies:**
   - Open a terminal or SSH into your Raspberry Pi.
   - Update the package lists by running the following command:
     ```
     sudo apt-get update
     ```
   - Install the required packages by running the following command:
     ```
     sudo apt-get install python3 python3-setuptools python3-pip bluetooth libbluetooth-dev libusb-1.0-0-dev
     ```
   - Install the Python package dependencies by running the following command:
     ```
     sudo pip3 install -r requirements.txt
     ```

2. **Run the app:**
   - Navigate to the project directory where `app.py` is located.
   - Execute the following command to start the Flask application:
     ```
     python3 app.py
     ```
   
   The Flask application will start running, and you should see output similar to the following:
   ```
   * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
   ```
