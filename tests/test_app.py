"""API checks for real inference and invalid public requests."""
import json
import unittest

import numpy as np
import pandas as pd

from app import create_app
from model_service import get_options, load_artifacts


class PredictionApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.example = get_options()["example"]

    def setUp(self):
        self.client = self.app.test_client()

    def test_frontend_and_assets_are_served(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"property-form", response.data)
        for path in ["/static/app.js", "/static/styles.css"]:
            with self.client.get(path) as asset:
                self.assertEqual(asset.status_code, 200)

    def test_model_is_ready(self):
        self.assertEqual(self.client.get("/api/health").json["status"], "ready")

    def test_prediction_matches_saved_pipeline(self):
        response = self.client.post("/api/predict", json=self.example)
        self.assertEqual(response.status_code, 200)
        pipeline, frame = load_artifacts()
        expected = float(np.expm1(pipeline.predict(pd.DataFrame([self.example], columns=frame.columns)))[0])
        self.assertAlmostEqual(response.json["price_crore"], expected, places=12)
        self.assertEqual(response.json["price_rupees"], round(expected * 10_000_000))
        self.assertAlmostEqual(response.json["illustrative_range_crore"]["low"], expected * 0.9)
        self.assertIn("not a statistical", response.json["range_description"])

    def test_invalid_numeric_inputs(self):
        for key, value in [("built_up_area", -1), ("built_up_area", float("nan")),
                           ("bedRoom", 1.5), ("bathroom", True),
                           ("servant room", 2), ("built_up_area", "850"),
                           ("bedRoom", 10 ** 400)]:
            with self.subTest(key=key, value=value):
                response = self.client.post("/api/predict", json={**self.example, key: value})
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.json)

    def test_other_cities_and_invalid_categories_are_rejected(self):
        for key, value in [("sector", "Mumbai"), ("furnishing_type", "unknown")]:
            with self.subTest(key=key):
                response = self.client.post("/api/predict", json={**self.example, key: value})
                self.assertEqual(response.status_code, 400)

    def test_missing_extra_and_non_object_inputs(self):
        missing = {key: value for key, value in self.example.items() if key != "sector"}
        for payload in [missing, {**self.example, "city": "Mumbai"}, [], None]:
            with self.subTest(payload=payload):
                response = self.client.post("/api/predict", data=json.dumps(payload), content_type="application/json")
                self.assertEqual(response.status_code, 400)

    def test_malformed_json_and_wrong_content_type(self):
        response = self.client.post("/api/predict", data="{bad", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)
        self.assertEqual(self.client.post("/api/predict", data="hello").status_code, 415)

    def test_large_requests_are_rejected(self):
        response = self.client.post("/api/predict", data='{"padding":"' + "x" * 17000 + '"}', content_type="application/json")
        self.assertEqual(response.status_code, 413)


if __name__ == "__main__":
    unittest.main()
