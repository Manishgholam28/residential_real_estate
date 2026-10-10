# Gurgaon property price estimator

An HTML/CSS/JavaScript frontend and Flask prediction API using a Scikit-learn Random Forest pipeline. Coverage: Gurgaon flats and independent houses. The research notebooks also contain EDA, feature engineering, and recommendation experiments.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe train_model.py
.\.venv\Scripts\python.exe app.py
```

Open http://localhost:8000. Model artifacts are generated locally and excluded from Git; the prepared training dataset and deterministic training script are included. An existing local checkout with working model artifacts does not need to retrain before opening the application.

## CI/CD and AWS

Read [AWS_CICD_GUIDE.md](AWS_CICD_GUIDE.md) for the first push, account setup, public deployment, and interview explanation.

The GitHub Actions workflow rebuilds the model artifacts, tests the API, and tests the Docker container. Once AWS repository variables are configured, successful changes on `main` publish a versioned image to Amazon ECR and deploy it through Amazon ECS Express Mode. Pull requests run CI without deployment. AWS access uses temporary OIDC credentials.

**Status:** CI/CD files are implemented. A successful GitHub Actions run and an authenticated AWS deployment still need to be performed in your accounts. No public AWS URL is claimed by this repository.

## Check the API

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for the API schema and local container commands. The displayed ±10% band is an illustrative range, not a statistically calibrated prediction interval.
