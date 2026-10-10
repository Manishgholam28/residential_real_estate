"""
Rebuilds gurgaon_properties_post_feature_selection_v2.csv (referenced by
model-selection.ipynb / insights-module.ipynb but never saved to disk by any
notebook in this project) and trains the final RandomForest pipeline exactly
as done in the "Exporting the model" section of model-selection.ipynb.

Produces: pipeline.pkl, df.pkl
"""
import argparse
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent


def categorize_luxury(score):
    if 0 <= score < 50:
        return "Low"
    elif 50 <= score < 150:
        return "Medium"
    elif 150 <= score <= 175:
        return "High"
    return None


def categorize_floor(floor):
    if 0 <= floor <= 2:
        return "Low Floor"
    elif 3 <= floor <= 10:
        return "Mid Floor"
    elif 11 <= floor <= 51:
        return "High Floor"
    return None


def build_v2_dataset(output_dir=ROOT):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ROOT / "gurgaon_properties_missing_value_imputation.csv")
    train_df = df.drop(columns=["society", "price_per_sqft"])
    train_df["luxury_category"] = train_df["luxury_score"].apply(categorize_luxury)
    train_df["floor_category"] = train_df["floorNum"].apply(categorize_floor)
    train_df.drop(columns=["floorNum", "luxury_score"], inplace=True)
    export_df = train_df.drop(columns=["pooja room", "study room", "others"])
    export_df.to_csv(output_dir / "gurgaon_properties_post_feature_selection_v2.csv", index=False)
    return export_df


def train(output_dir=ROOT):
    output_dir = Path(output_dir)
    df = build_v2_dataset(output_dir)
    df["furnishing_type"] = df["furnishing_type"].replace(
        {0.0: "unfurnished", 1.0: "semifurnished", 2.0: "furnished"}
    )

    X = df.drop(columns=["price"])
    y = df["price"]
    y_transformed = np.log1p(y)

    columns_to_encode = [
        "property_type",
        "sector",
        "balcony",
        "agePossession",
        "furnishing_type",
        "luxury_category",
        "floor_category",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                StandardScaler(),
                ["bedRoom", "bathroom", "built_up_area", "servant room", "store room"],
            ),
            ("cat", OrdinalEncoder(), columns_to_encode),
            (
                "cat1",
                OneHotEncoder(drop="first", sparse_output=False),
                ["sector", "agePossession"],
            ),
        ],
        remainder="passthrough",
    )

    pipeline = Pipeline(
        [
            ("preprocessor", preprocessor),
            ("regressor", RandomForestRegressor(n_estimators=500, random_state=42)),
        ]
    )

    pipeline.fit(X, y_transformed)

    with (output_dir / "pipeline.pkl").open("wb") as file:
        pickle.dump(pipeline, file)
    with (output_dir / "df.pkl").open("wb") as file:
        pickle.dump(X, file)

    print("Saved pipeline.pkl and df.pkl")
    print("Training rows:", X.shape[0])
    sample = X.iloc[[0]]
    pred = np.expm1(pipeline.predict(sample))[0]
    print(f"Sanity check prediction for row 0: {pred:.2f} Cr (actual: {y.iloc[0]:.2f} Cr)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rebuild the final Random Forest artifacts.")
    parser.add_argument("--output-dir", type=Path, default=ROOT,
                        help="Artifact destination; use a separate directory for verification.")
    train(parser.parse_args().output_dir)
