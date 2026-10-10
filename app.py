"""Flask frontend and prediction API. Run with python app.py."""
import logging
import os

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from model_service import get_options, load_artifacts, predict_price


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    app.json.sort_keys = False

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        try:
            load_artifacts()
        except Exception:
            app.logger.exception("Model readiness check failed")
            return jsonify(status="unavailable"), 503
        return jsonify(status="ready", coverage="Gurgaon")

    @app.get("/api/options")
    def options():
        try:
            return jsonify(get_options())
        except Exception:
            app.logger.exception("Could not load property options")
            return jsonify(error="The prediction service is unavailable. Please try again later."), 503

    @app.post("/api/predict")
    def predict():
        if not request.is_json:
            return jsonify(error="Send the property details as JSON."), 415
        payload = request.get_json()
        try:
            return jsonify(predict_price(payload))
        except ValueError as error:
            return jsonify(error=str(error)), 400
        except Exception:
            app.logger.exception("Prediction failed")
            return jsonify(error="We could not estimate this property. Please try again later."), 503

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith("/api/"):
            return jsonify(error=error.description), error.code
        return error

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
            "base-uri 'self'; form-action 'self'"
        )
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    return app


app = create_app()

if __name__ == "__main__":
    from waitress import serve

    logging.basicConfig(level=logging.INFO)
    load_artifacts()
    port = int(os.environ.get("PORT", "8000"))
    print(f"Property price predictor: http://localhost:{port}", flush=True)
    serve(app, host=os.environ.get("HOST", "127.0.0.1"), port=port, threads=4)
