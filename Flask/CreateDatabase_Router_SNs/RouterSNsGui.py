#import paramiko
import sqlite3
from flask import Flask, render_template

app = Flask(__name__)

# Replace these with your actual details
ROUTER_IP = '192.168.1.1'
ROUTER_USERNAME = 'admin'
ROUTER_PASSWORD = 'password'
ROUTER_SERIAL_COMMAND = 'show version | include Serial number'

# Function to query the router and get the serial number
def query_router_serial(router_ip, username, password, command):
    serial_number = None
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(router_ip, username=username, password=password)
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8')
    # You'll need to parse the output to extract the serial number
    # This depends on the command output format
    serial_number = output.strip() # This is a placeholder
    ssh.close()
    return serial_number

# Function to insert the serial number into the SQLite database
def insert_serial_number_into_db(serial_number):
    conn = sqlite3.connect('routers.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS router_serials (serial TEXT)''')
    c.execute('''INSERT INTO router_serials (serial) VALUES (?)''', (serial_number,))
    conn.commit()
    conn.close()

# Function to get all serial numbers from the SQLite database
def get_serial_numbers_from_db():
    conn = sqlite3.connect('routers.db')
    c = conn.cursor()
    c.execute('''SELECT serial FROM router_serials''')
    serial_numbers = c.fetchall()
    conn.close()
    return serial_numbers

# Route to display the serial numbers
@app.route('/')
def index():
    serial_numbers = get_serial_numbers_from_db()
    return render_template('index.html', serial_numbers=serial_numbers)

if __name__ == '__main__':
    # Get the serial number and store it in the database
    # Note: In a production system, you'd have proper error handling and possibly a scheduled job to do this
    serial_number = 'ZNPPPTNZ8'#query_router_serial(ROUTER_IP, ROUTER_USERNAME, ROUTER_PASSWORD, ROUTER_SERIAL_COMMAND)
    insert_serial_number_into_db(serial_number)

    # Run the Flask app
    app.run(debug=True, port=5001)
