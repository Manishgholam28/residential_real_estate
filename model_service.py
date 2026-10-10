"""Inference using the existing trusted local Scikit-learn artifacts."""
from functools import lru_cache
from pathlib import Path
import math
import pickle

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
CATEGORICAL = (
    "property_type", "sector", "balcony", "agePossession",
    "furnishing_type", "luxury_category", "floor_category",
)
NUMERIC = {
    "bedRoom": (1, 20, True), "bathroom": (1, 20, True),
    "built_up_area": (100, 20000, False),
    "servant room": (0, 1, True), "store room": (0, 1, True),
}
LABELS = {
    "bedRoom": "Bedrooms", "bathroom": "Bathrooms",
    "built_up_area": "Built-up area", "servant room": "Servant room",
    "store room": "Store room", "property_type": "Property type",
    "sector": "Sector", "balcony": "Balconies",
    "agePossession": "Age / possession", "furnishing_type": "Furnishing",
    "luxury_category": "Luxury category", "floor_category": "Floor category",
}


@lru_cache(maxsize=1)
def load_artifacts():
    with (ROOT / "pipeline.pkl").open("rb") as file:
        pipeline = pickle.load(file)
    with (ROOT / "df.pkl").open("rb") as file:
        frame = pickle.load(file)
    if set(frame.columns) != set(CATEGORICAL) | set(NUMERIC):
        raise RuntimeError("The saved input schema is incompatible with this application.")
    return pipeline, frame


@lru_cache(maxsize=1)
def get_options():
    _, frame = load_artifacts()
    choices = {column: sorted(str(value) for value in frame[column].dropna().unique())
               for column in CATEGORICAL}
    return {
        "coverage": "Gurgaon", "choices": choices,
        "limits": {column: {"min": low, "max": high, "integer": integer}
                   for column, (low, high, integer) in NUMERIC.items()},
        "example": {
            "property_type": "flat", "sector": "sector 36", "bedRoom": 3,
            "bathroom": 2, "balcony": "2", "agePossession": "New Property",
            "built_up_area": 850, "servant room": 0, "store room": 0,
            "furnishing_type": "unfurnished", "luxury_category": "Low",
            "floor_category": "Low Floor",
        },
    }


def validate_property(payload):
    if not isinstance(payload, dict):
        raise ValueError("Enter the property details as a JSON object.")
    expected = set(CATEGORICAL) | set(NUMERIC)
    missing = expected - payload.keys()
    if missing:
        raise ValueError("Please provide: " + ", ".join(LABELS[key] for key in sorted(missing)) + ".")
    if payload.keys() - expected:
        raise ValueError("The request includes unsupported property fields.")
    choices = get_options()["choices"]
    clean = {}
    for column in CATEGORICAL:
        value = payload[column]
        if not isinstance(value, str) or value not in choices[column]:
            raise ValueError(f"Select a supported value for {LABELS[column]}.")
        clean[column] = value
    for column, (low, high, integer) in NUMERIC.items():
        value = payload[column]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{LABELS[column]} must be a number.")
        if not low <= value <= high or not math.isfinite(value):
            raise ValueError(f"{LABELS[column]} must be between {low} and {high}.")
        if integer and value != int(value):
            raise ValueError(f"{LABELS[column]} must be a whole number.")
        clean[column] = int(value) if integer else float(value)
    return clean


def predict_price(payload):
    values = validate_property(payload)
    pipeline, frame = load_artifacts()
    sample = pd.DataFrame([values], columns=frame.columns)
    price = float(np.expm1(pipeline.predict(sample))[0])
    if not math.isfinite(price) or price <= 0:
        raise RuntimeError("The model returned an invalid price.")
    return {
        "price_crore": price, "price_rupees": round(price * 10_000_000),
        "illustrative_range_crore": {"low": price * 0.9, "high": price * 1.1},
        "range_description": "A fixed ±10% illustration, not a statistical prediction interval.",
        "coverage": "Gurgaon", "property": values,
    }
