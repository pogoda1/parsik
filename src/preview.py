from flask import Flask, render_template
import json
from datetime import datetime

app = Flask(__name__)

def load_parser_list():
    try:
        with open('data/parserList.json', 'r', encoding='utf-8') as file:
            return json.load(file)['data']
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def format_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%d.%m.%Y %H:%M')
    except:
        return date_str

@app.route('/')
def index():
    events = load_parser_list()
    return render_template('preview.html', events=events, format_date=format_date)

if __name__ == '__main__':
    app.run(debug=True, port=5555) 