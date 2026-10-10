import pickle

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Gurgaon Real Estate Price Predictor", page_icon="🏠")


@st.cache_resource
def load_artifacts():
    with open("pipeline.pkl", "rb") as file:
        pipeline = pickle.load(file)
    with open("df.pkl", "rb") as file:
        df = pickle.load(file)
    return pipeline, df


try:
    pipeline, df = load_artifacts()
except FileNotFoundError:
    st.error(
        "pipeline.pkl / df.pkl not found. Run price_prediction_backend.ipynb "
        "first (top to bottom) to train the model and generate them."
    )
    st.stop()

st.title("🏠 Gurgaon Real Estate Price Predictor")
st.caption("Enter the property details below to get an estimated price.")

col1, col2 = st.columns(2)

with col1:
    property_type = st.selectbox("Property Type", sorted(df["property_type"].unique()))
    sector = st.selectbox("Sector", sorted(df["sector"].unique()))
    bedrooms = st.number_input("Bedrooms", min_value=1, max_value=20, value=3, step=1)
    bathrooms = st.number_input("Bathrooms", min_value=1, max_value=20, value=2, step=1)
    balcony = st.selectbox("Balconies", sorted(df["balcony"].unique()))
    age_possession = st.selectbox("Age / Possession", sorted(df["agePossession"].unique()))

with col2:
    built_up_area = st.number_input(
        "Built-up Area (sqft)", min_value=100.0, max_value=20000.0, value=1000.0, step=50.0
    )
    servant_room = st.selectbox("Servant Room", [0.0, 1.0])
    store_room = st.selectbox("Store Room", [0.0, 1.0])
    furnishing_type = st.selectbox("Furnishing Type", ["unfurnished", "semifurnished", "furnished"])
    luxury_category = st.selectbox("Luxury Category", ["Low", "Medium", "High"])
    floor_category = st.selectbox("Floor Category", ["Low Floor", "Mid Floor", "High Floor"])

if st.button("Predict Price", type="primary"):
    input_df = pd.DataFrame(
        [
            [
                property_type,
                sector,
                bedrooms,
                bathrooms,
                balcony,
                age_possession,
                built_up_area,
                servant_room,
                store_room,
                furnishing_type,
                luxury_category,
                floor_category,
            ]
        ],
        columns=df.columns,
    )

    prediction = np.expm1(pipeline.predict(input_df))[0]
    low, high = prediction * 0.9, prediction * 1.1

    st.success(f"Estimated Price: ₹{prediction:.2f} Cr")
    st.write(f"Likely range: ₹{low:.2f} Cr – ₹{high:.2f} Cr")
