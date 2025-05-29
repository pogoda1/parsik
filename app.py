from flask import Flask, jsonify, render_template_string
from api import call_model_api
from utils import load_test_data, get_event_by_id
from templates import MAIN_TEMPLATE

app = Flask(__name__)

@app.route("/")
def index():
    return render_template_string(MAIN_TEMPLATE)

@app.route("/get_events", methods=["GET"])
def get_events():
    data = load_test_data()
    if not data:
        return jsonify({"error": "test.json не найден"}), 404
    return jsonify(data.get("data", []))

@app.route("/process_single/<string:event_id>", methods=["GET"])
def process_single(event_id):
    print(f"[DEBUG] Processing event_id: {event_id}")
    data = load_test_data()
    if not data:
        print("[ERROR] test.json not found")
        return jsonify({"error": "test.json не найден"}), 404
    
    event = get_event_by_id(event_id, data)
    if not event:
        print(f"[ERROR] Event {event_id} not found")
        return jsonify({"error": "Событие не найдено"}), 404
    
    text = event.get("input", "")
    print(f"[DEBUG] Event text: {text[:100]}...")  # First 100 chars
    model_result = call_model_api(text)
    print(f"[DEBUG] Model result: {model_result}")
    return jsonify(model_result)

if __name__ == "__main__":
    app.run(debug=True) 