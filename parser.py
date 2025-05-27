from flask import Flask, jsonify, render_template_string
import requests
import json
import os

app = Flask(__name__)

API_URL = "http://localhost:1234/v1/chat/completions"
PROMPT_FILE = os.path.expanduser("/Users/matvey/Documents/obsidian/Стартап/Разработка/parserEventAI/prompt/prompt.md")
TEST_JSON_PATH = "test.json"

with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    PROMPT = f.read()

def check_for_errors(parsed_json):
    if isinstance(parsed_json, dict) and "errorCode" in parsed_json:
        return parsed_json["errorText"]
    return None

def call_model_api(text):
    full_prompt = f"{PROMPT}\n\n{text}"
    headers = {"Content-Type": "application/json"}
    request_data = {
        "model": "gemma-3-4b-it-qat",
        "messages": [
            {"role": "system", "content": "You are an assistant that extracts structured JSON from unstructured text."},
            {"role": "user", "content": full_prompt}
        ],
        "temperature": 0.0
    }
    try:
        response = requests.post(API_URL, json=request_data, headers=headers, timeout=15)
        response.raise_for_status()
        res_json = response.json()
        content = res_json["choices"][0]["message"]["content"]
        content = content.replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(content)
        err_text = check_for_errors(parsed_json)
        if err_text:
            return {"error": err_text}
        return {"result": parsed_json}
    except Exception as e:
        return {"error": f"Ошибка при вызове модели: {str(e)}"}

@app.route("/")
def index():
    # Простейшая страница с кнопкой и пустым контейнером для вывода результата
    return render_template_string("""
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<title>Обработка событий AI</title>
<style>
  body { font-family: Arial, sans-serif; margin: 20px; }
  button { font-size: 16px; padding: 10px 20px; }
  pre { background: #f0f0f0; padding: 10px; white-space: pre-wrap; max-height: 500px; overflow-y: auto; }
  .error { color: red; }
</style>
</head>
<body>
  <h1>Обработка событий AI</h1>
  <button id="loadBtn">Загрузить и обработать события</button>
  <div id="output"></div>

<script>
  const btn = document.getElementById('loadBtn');
  const output = document.getElementById('output');

  btn.addEventListener('click', () => {
    output.innerHTML = 'Загрузка...';
    fetch('/process_all')
      .then(res => res.json())
      .then(data => {
        if (!Array.isArray(data)) {
          output.innerHTML = '<p class="error">Ошибка сервера или файл не найден.</p>';
          return;
        }
        let html = '';
        data.forEach(item => {
          html += `<h2>Событие ID: ${item.id}</h2>`;
          html += `<p><strong>Исходный текст:</strong><br>${item.text.replace(/\\n/g,'<br>')}</p>`;
          if(item.parse_result.error){
            html += `<p class="error"><strong>Ошибка:</strong> ${item.parse_result.error}</p>`;
          } else {
            html += `<pre>${JSON.stringify(item.parse_result.result, null, 2)}</pre>`;
          }
          html += '<hr>';
        });
        output.innerHTML = html;
      })
      .catch(err => {
        output.innerHTML = '<p class="error">Ошибка при загрузке: ' + err.message + '</p>';
      });
  });
</script>
</body>
</html>
""")

@app.route("/process_all", methods=["GET"])
def process_all():
    if not os.path.exists(TEST_JSON_PATH):
        return jsonify({"error": "test.json не найден"}), 404
    with open(TEST_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    for item in data.get("data", []):
        text = item.get("text", "")
        model_result = call_model_api(text)
        results.append({
            "id": item.get("id"),
            "text": text,
            "parse_result": model_result
        })

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
