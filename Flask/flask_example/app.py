from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_name = request.form['name']
        return render_template('greet.html', name=user_name)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
