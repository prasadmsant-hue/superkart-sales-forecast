import io
import os

import pandas as pd
import requests
import streamlit as st

# Backend URL: the Flask container on the same Docker network (overridable by environment variable)
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:7860")
REFERENCE_YEAR = 2025  # Store_Age_Years = REFERENCE_YEAR - establishment year (as in training)

PRODUCT_TYPES = ["Baking Goods", "Breads", "Breakfast", "Canned", "Dairy", "Frozen Foods",
                 "Fruits and Vegetables", "Hard Drinks", "Health and Hygiene", "Household",
                 "Meat", "Others", "Seafood", "Snack Foods", "Soft Drinks", "Starchy Foods"]
PERISHABLES = ["Dairy", "Meat", "Fruits and Vegetables", "Breads", "Breakfast", "Seafood"]
DRINKS = ["Hard Drinks", "Soft Drinks"]
NON_CONSUMABLES = ["Health and Hygiene", "Household", "Others"]

# Existing SuperKart stores and their fixed attributes: (size, city tier, type, establishment year)
STORES = {
    "OUT001 - Supermarket Type1, Tier 2": ("High", "Tier 2", "Supermarket Type1", 1987),
    "OUT002 - Food Mart, Tier 3": ("Small", "Tier 3", "Food Mart", 1998),
    "OUT003 - Departmental Store, Tier 1": ("Medium", "Tier 1", "Departmental Store", 1999),
    "OUT004 - Supermarket Type2, Tier 2": ("Medium", "Tier 2", "Supermarket Type2", 2009),
}
BATCH_COLUMNS = ["Product_Weight", "Product_Sugar_Content", "Product_Allocated_Area", "Product_MRP",
                 "Store_Size", "Store_Location_City_Type", "Store_Type", "Product_Id_char",
                 "Store_Age_Years", "Product_Type_Category"]

st.set_page_config(page_title="SuperKart Sales Forecast", page_icon="🛒")
st.title("SuperKart Sales Forecast")
st.write("Forecast the sales revenue of a product in a SuperKart store for the coming quarter.")

# ---------------- Online prediction ----------------
st.subheader("Online Prediction")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Product**")
    product_type = st.selectbox("Product Type", PRODUCT_TYPES, index=PRODUCT_TYPES.index("Fruits and Vegetables"))
    if product_type in NON_CONSUMABLES:
        sugar_content = "No Sugar"
        st.caption("Sugar content: No Sugar (non-consumable product)")
    else:
        sugar_content = st.selectbox("Sugar Content", ["Low Sugar", "Regular"])
    product_weight = st.number_input("Product Weight", min_value=1.0, max_value=30.0, value=12.66, step=0.1)
    product_mrp = st.number_input("Product MRP", min_value=10.0, max_value=400.0, value=147.0, step=1.0)
    allocated_area = st.number_input("Allocated Display Area (share of store display area)",
                                     min_value=0.001, max_value=0.5, value=0.068, step=0.001, format="%.3f")

with col2:
    st.markdown("**Store**")
    store_choice = st.selectbox("Store", list(STORES) + ["Other / new store"])
    if store_choice in STORES:
        store_size, city_tier, store_type, est_year = STORES[store_choice]
        st.caption(f"Size: {store_size} | City: {city_tier} | Type: {store_type} | Established: {est_year}")
    else:
        store_size = st.selectbox("Store Size", ["Small", "Medium", "High"])
        city_tier = st.selectbox("City Type", ["Tier 1", "Tier 2", "Tier 3"])
        store_type = st.selectbox("Store Type", ["Departmental Store", "Food Mart",
                                                 "Supermarket Type1", "Supermarket Type2"])
        est_year = st.number_input("Establishment Year", min_value=1950, max_value=REFERENCE_YEAR, value=2005, step=1)
        st.caption("Combinations not present in the history are extrapolated; treat the forecast as indicative.")

# Derive the model features from the business inputs
if product_type in DRINKS:
    product_id_char = "DR"
elif product_type in NON_CONSUMABLES:
    product_id_char = "NC"
else:
    product_id_char = "FD"

payload = {
    "Product_Weight": product_weight,
    "Product_Sugar_Content": sugar_content,
    "Product_Allocated_Area": allocated_area,
    "Product_MRP": product_mrp,
    "Store_Size": store_size,
    "Store_Location_City_Type": city_tier,
    "Store_Type": store_type,
    "Product_Id_char": product_id_char,
    "Store_Age_Years": REFERENCE_YEAR - int(est_year),
    "Product_Type_Category": "Perishables" if product_type in PERISHABLES else "Non Perishables",
}

if st.button("Predict", type="primary"):
    try:
        response = requests.post(f"{BACKEND_URL}/v1/predict", json=payload, timeout=30)
        if response.status_code == 200:
            st.success(f"Forecast sales revenue: {response.json()['Predicted_Sales']:,.2f}")
        else:
            st.error(f"The API returned an error ({response.status_code}): {response.text}")
    except requests.exceptions.RequestException as err:
        st.error(f"Unable to connect to the prediction API: {err}")

# ---------------- Batch prediction ----------------
st.subheader("Batch Prediction")
st.write("Upload a CSV file with these columns: " + ", ".join(f"`{c}`" for c in BATCH_COLUMNS))
uploaded_file = st.file_uploader("Upload CSV file for batch prediction", type=["csv"])

if uploaded_file is not None:
    if st.button("Predict Batch", type="primary"):
        file_bytes = uploaded_file.getvalue()
        try:
            response = requests.post(f"{BACKEND_URL}/v1/predictbatch",
                                     files={"file": (uploaded_file.name, file_bytes, "text/csv")}, timeout=60)
            if response.status_code == 200:
                predictions = response.json()
                results = pd.read_csv(io.BytesIO(file_bytes))
                results["Predicted_Sales"] = [predictions[str(i)] for i in results.index]
                st.success(f"Forecast for {len(results)} products. Total: {results['Predicted_Sales'].sum():,.2f}")
                st.dataframe(results)
                st.download_button("Download predictions as CSV", results.to_csv(index=False),
                                   file_name="superkart_predictions.csv", mime="text/csv")
            else:
                st.error(f"The API returned an error ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as err:
            st.error(f"Unable to connect to the prediction API: {err}")
