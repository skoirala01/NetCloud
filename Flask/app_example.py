# Import the Flask class from the flask module
from flask import Flask

# Create an instance of the Flask class. This is our WSGI application.
app = Flask(__name__)

# Define a route for the root URL ("/"). This means that when someone visits the root URL,
# the function `index` will be called.
@app.route('/')
def index():
    # The function returns the text "Hello, World!" as a response.
    return 'Hello, World!'

# Check if the executed file is the main program and run the app.
if __name__ == '__main__':
    # Run the app on localhost port 5000. Set debug=True for debugging mode, which allows
    # you to see error messages in the browser and automatically reloads the server when
    # changes are made to the code.
    app.run(debug=True)
