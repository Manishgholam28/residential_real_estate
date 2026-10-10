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

The active workflow is [.github/workflows/main.yml](.github/workflows/main.yml). See [EC2_CICD_NOTES.md](EC2_CICD_NOTES.md) for its required secrets, EC2 runner, and port configuration.

On pushes to `main`, GitHub-hosted jobs rebuild the model artifacts, test the API and Docker container, and publish a uniquely tagged image to Amazon ECR. A self-hosted Linux x64 runner on EC2 pulls that image and replaces the application container. AWS access uses repository secrets. EC2 port 8080 maps to application port 8000. The workflow does not deploy pull requests.

**Status:** CI/CD files are implemented. A successful GitHub Actions run and an authenticated AWS deployment still need to be performed in your accounts. No public AWS URL is claimed by this repository.

## Check the API

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for the API schema and local container commands. The displayed ±10% band is an illustrative range, not a statistically calibrated prediction interval.
