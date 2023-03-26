from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    if request.method == 'POST':
        print("Data received from Webhook is: ", request.json)
        with open('variables.txt', 'w') as fp:
            fp.write(str(request.json))
        return "Webhook received!"

app.run(host='0.0.0.0', port=8000)