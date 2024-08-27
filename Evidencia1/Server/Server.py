from flask import Flask

app = Flask(__name__)

@app.route('/qhabido')
def hello_world():
    return 'Es un vrgazo de feria ando todo tatuado como Lil wayne'

if __name__ == '__main__':
    app.run(debug=True, port=5000)
