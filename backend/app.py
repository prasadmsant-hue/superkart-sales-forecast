import joblib
import pandas as pd
from flask import Flask, request, jsonify

# Initialize the Flask application
superkart_api = Flask("SuperKart Sales Forecasting API")

# Load the serialized pipeline (one-hot encoder + regression model)
model = joblib.load("superkart_model.joblib")

# The features the model was trained on, in the same order
FEATURES = [
    "Product_Weight", "Product_Allocated_Area", "Product_MRP", "Store_Age_Years",
    "Product_Sugar_Content", "Store_Size", "Store_Location_City_Type",
    "Store_Type", "Product_Id_char", "Product_Type_Category",
]


@superkart_api.get("/")
def home():
    """Health check: confirms the API is running."""
    return "Welcome to the SuperKart Sales Forecasting API!"


@superkart_api.post("/v1/predict")
def predict_sales():
    """Online inference: one product-store record as JSON -> predicted sales."""
    record = request.get_json()
    missing = [f for f in FEATURES if f not in record]
    if missing:
        return jsonify({"error": f"Missing features: {missing}"}), 400

    input_data = pd.DataFrame([{f: record[f] for f in FEATURES}])
    prediction = float(model.predict(input_data)[0])  # numpy float -> Python float for JSON

    return jsonify({"Predicted_Sales": round(prediction, 2)})


@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    """Batch inference: CSV file upload -> {row index: predicted sales}."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Send the CSV under the key 'file'."}), 400

    input_data = pd.read_csv(request.files["file"])
    missing = [f for f in FEATURES if f not in input_data.columns]
    if missing:
        return jsonify({"error": f"Missing columns: {missing}"}), 400

    predictions = model.predict(input_data[FEATURES])
    result = {str(idx): round(float(pred), 2) for idx, pred in zip(input_data.index, predictions)}
    return jsonify(result)


if __name__ == "__main__":
    superkart_api.run(debug=True, host="0.0.0.0", port=7860)
