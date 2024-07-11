"""
Flask-приложение для обработки вебхуков.

Приложение принимает POST-запросы и сохраняет данные в файл 'variables.txt'.

Возвращает:
Сообщение 'Webhook received!'.
"""
import logging
from flask import Flask, request

app = Flask(__name__)
@app.route('/', methods=['POST'])
def webhook():
    """
 Функция webhook обрабатывает POST-запросы.

 Если метод запроса POST, то приложение сохраняет данные запроса в файл 'variables.txt'.

 Возвращает:
 Сообщение 'Webhook received!'.
 """
    if request.method == 'POST':
        print("Data received from Webhook is: ", request.json)
        with open('variables.txt', 'w', encoding='utf-8') as fp:
            fp.write(str(request.json))
        return "Webhook received!"
    else:
        return "Method not allowed!"  # Добавлен возврат значения для других методов
logging.basicConfig(filename='error.log',level=logging.DEBUG) #logging
app.run(host='0.0.0.0', port=8000)
