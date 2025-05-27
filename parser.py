from flask import Flask, request, render_template_string, redirect, url_for, jsonify
import requests
import json
from datetime import datetime
import os
import webbrowser
import threading

app = Flask(__name__)

API_URL = "http://localhost:1234/v1/chat/completions"  
PROMPT_FILE = os.path.expanduser("/Users/matvey/Documents/obsidian/Стартап/Разработка/prompt.md")
with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    PROMPT = f.read()

HTML_RESULT = """
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8">
    <title>Результат</title>
  <style>
  textarea { width: 100%; height: 200px; }
  pre { background-color: #f4f4f4; padding: 10px; border: 1px solid #ccc; }
  .reset-btn { 
    margin-top: 20px;
    padding: 10px 20px;
    background-color: #f44336;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  .reset-btn:hover {
    background-color: #d32f2f;
  }
  .event-block {
    margin-bottom: 20px;
    padding: 15px;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  .event-block h3 {
    margin-top: 0;
  }
  #results-container {
    margin-top: 20px;
  }
  .loading {
    display: none;
    margin: 20px 0;
    color: #666;
  }
</style>
  </head>
  <body>
    <h1>Парсинг мероприятий</h1>
    <div id="results-container"></div>
    <div id="loading" class="loading">Обработка следующего события...</div>
    
    <form>
      <button type="button" onclick="window.location.reload()" class="reset-btn">Начать заново</button>
      <button type="button" onclick="copyToClipboard()" class="reset-btn" style="background-color: #4CAF50; margin-left: 10px;">Скопировать все результаты</button>
    </form>

    <script>
    let currentIndex = 0;
    const events = {{ events|tojson|safe }};
    
    function addResultBlock(result) {
        const container = document.getElementById('results-container');
        const block = document.createElement('div');
        block.className = 'event-block';
        block.innerHTML = `
            <h3>Событие #${currentIndex + 1}</h3>
            <p><b>Оригинальный текст:</b></p>
            <textarea readonly>${result.original}</textarea>
            <p><b>Результат парсинга:</b></p>
            <pre>${result.parsed || result.error}</pre>
        `;
        container.appendChild(block);
    }

    function processNextEvent() {
        if (currentIndex >= events.length) {
            document.getElementById('loading').style.display = 'none';
            return;
        }

        document.getElementById('loading').style.display = 'block';
        
        fetch('/process_event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: events[currentIndex].text,
                index: currentIndex
            })
        })
        .then(response => response.json())
        .then(result => {
            addResultBlock(result);
            currentIndex++;
            processNextEvent();
        })
        .catch(error => {
            console.error('Error:', error);
            addResultBlock({
                original: events[currentIndex].text,
                error: 'Ошибка обработки: ' + error
            });
            currentIndex++;
            processNextEvent();
        });
    }

    function copyToClipboard() {
        const results = Array.from(document.querySelectorAll('.event-block')).map(block => ({
            original: block.querySelector('textarea').value,
            parsed: block.querySelector('pre').textContent
        }));
        const jsonText = JSON.stringify(results, null, 2);
        navigator.clipboard.writeText(jsonText).then(() => {
            alert('Результаты скопированы в буфер обмена');
        }).catch(err => {
            console.error('Ошибка копирования:', err);
        });
    }

    // Start processing when page loads
    window.onload = processNextEvent;
    </script>
  </body>
</html>
"""

def load_test_data():
    with open('test.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route("/process_event", methods=["POST"])
def process_event():
    data = request.json
    text = data['text']
    
    if not text:
        return jsonify({
            "original": text,
            "error": "Пустой текст"
        })
    
    full_prompt = f"{PROMPT}\n\n{text}"
    
    headers = {"Content-Type": "application/json"}
    request_data = {
        "model": "gemma-3-4b-it-qat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that can parse unstructured text into structured JSON."},
            {"role": "user", "content": full_prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(API_URL, headers=headers, json=request_data)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            content = content.replace("```json", "").replace("```", "").strip()
            try:
                json.loads(content)  # Validate JSON
                return jsonify({
                    "original": text,
                    "parsed": content
                })
            except json.JSONDecodeError:
                return jsonify({
                    "original": text,
                    "error": f"Invalid JSON format: {content}"
                })
        else:
            return jsonify({
                "original": text,
                "error": f"Request error: {response.status_code}"
            })
    except Exception as e:
        return jsonify({
            "original": text,
            "error": f"Processing error: {str(e)}"
        })

@app.route("/", methods=["GET", "POST"])
def index():
    test_data = load_test_data()
    return render_template_string(HTML_RESULT, events=test_data['data'])

if __name__ == "__main__":
    def open_browser():
        webbrowser.open("http://127.0.0.1:5000/")
    threading.Timer(1, open_browser).start()
    app.run()
