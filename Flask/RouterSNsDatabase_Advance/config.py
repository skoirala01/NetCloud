# config.py

# Router details
ROUTERS = [
    {
        'ip': '192.168.1.1',
        'username': 'admin',
        'password': 'password',
        'command': 'show version | include Serial number'
    },
    # Add more router dictionaries if needed
]

# Database details
SQLALCHEMY_DATABASE_URI = 'sqlite:///routers.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
