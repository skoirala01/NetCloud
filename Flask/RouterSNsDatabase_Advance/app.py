# app.py

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
#import paramiko
import logging
from config import ROUTERS, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS

try:
    from flask_sqlalchemy import SQLAlchemy
except:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask_sqlalchemy'])
    from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

db = SQLAlchemy(app)

class Router(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(15), unique=True, nullable=False)
    serial_number = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Router {self.ip}>'

# Function to query the router and get the serial number
def query_router_serial(router):
    serial_number = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(router['ip'], username=router['username'], password=router['password'])
        stdin, stdout, stderr = ssh.exec_command(router['command'])
        output = stdout.read().decode('utf-8')
        # Parse the output to extract the serial number
        serial_number = output.strip()  # Update with proper parsing
        ssh.close()
    except Exception as e:
        logging.error(f"Error querying {router['ip']}: {e}")
    return serial_number

# Function to update the database with the serial number
def update_router_info(router, serial_number):
    router_entry = Router.query.filter_by(ip=router['ip']).first()
    print(100,router_entry.ip)
    if router_entry:
        router_entry.serial_number = serial_number
        print(router_entry.serial_number)
    else:
        router_entry = Router(ip=router['ip'], serial_number=serial_number)
        db.session.add(router_entry)
    db.session.commit()

# Route to display the serial numbers
@app.route('/')
def index():
    routers = Router.query.all()
    return render_template('index.html', routers=routers)

# Initialize the database and query routers
def init_db_and_routers():
    db.create_all()
    for router in ROUTERS:
        print(router)
        serial_number = '1AAAAAAA'#query_router_serial(router)
        #serial_number = query_router_serial(router)
        if serial_number:
            print(serial_number)
            update_router_info(router, serial_number)

if __name__ == '__main__':
    with app.app_context():
        #db.create_all()
        logging.basicConfig(level=logging.INFO)
        init_db_and_routers()
        app.run(debug=True, port = 5002)
