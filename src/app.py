from flask import Flask, jsonify, render_template_string
from src.api import ModelAPI
from .utils import DataLoader
from .templates import MAIN_TEMPLATE
from .sync import getListForSync ,fillLocalList
app = Flask(__name__)
model_api = ModelAPI()
data_loader = DataLoader()

@app.route("/")
def index():
    return render_template_string(MAIN_TEMPLATE)

@app.route("/get_events", methods=["GET"])
async def get_events():
    list = await getListForSync()
    fillLocalList(list)
    data = data_loader.load_test_data()
    if not data:
        return jsonify({"error": "test.json не найден"}), 404
    return jsonify(data.get("data", []))

@app.route("/process_single/<string:event_id>", methods=["GET"])
async def process_single(event_id):
    data = data_loader.load_test_data()
    if not data:
        return jsonify({"error": "test.json не найден"}), 404
    
    event = data_loader.get_event_by_id(event_id, data)
    if not event:
        return jsonify({"error": "Событие не найдено"}), 404
    
    text = event.get("input", "")
    model_result = await model_api.call_model_api(text)
    return jsonify(model_result)

if __name__ == "__main__":
    app.run(debug=True) 