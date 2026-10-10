# Run and deploy the property price estimator

The main application now uses HTML, CSS, and JavaScript with a Flask API. Streamlit is not used by the new application. The existing `pipeline.pkl` is used for real predictions, and the supported market remains Gurgaon.

## Open the local frontend

From this project folder in PowerShell:

```powershell
.\.venv\Scripts\python.exe app.py
```

Open **http://localhost:8000**. Keep the server running while demonstrating. Click **Load example**, then **Estimate property price**. Startup loads the saved model and may take several seconds.

For a fresh checkout, create a virtual environment and install the requirements first:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe train_model.py
.\.venv\Scripts\python.exe app.py
```

The application resolves model and template paths relative to its source directory, so launching it from a different working directory also works. `HOST` and `PORT` are configurable environment variables. The local default is `127.0.0.1:8000`; container deployments use `0.0.0.0:8000`.

## Build the deployable container

Start Docker Desktop with Linux containers enabled, then run:

```powershell
docker build --platform linux/amd64 -t gurgaon-property-estimator .
docker run --name gurgaon-property-estimator --rm -p 8000:8000 gurgaon-property-estimator
```

Open http://localhost:8000 and check http://localhost:8000/api/health. The Docker build includes the trained artifacts and frontend, and excludes notebooks, raw datasets, local credentials, and the virtual environment. The application uses Waitress, with one model instance per server process. Generate both model files before building from a fresh checkout.

The Docker daemon must be running to build and test the container. Having the Docker CLI installed alone is insufficient. Container execution needs separate verification from the local Python checks.

## Public AWS deployment

**Status:** `.github/workflows/main.yml` is implemented; a public service still needs a successful run in your AWS account. See [EC2_CICD_NOTES.md](EC2_CICD_NOTES.md) for the chosen ECR and EC2 approach.

The workflow rebuilds the model from the versioned prepared dataset, tests the API and container, and pushes a uniquely tagged image to Amazon ECR. A self-hosted Linux x64 runner installed on EC2 pulls the image and runs `mltest` with port mapping `8080:8000`. AWS authentication uses GitHub repository secrets. After successful deployment, verify `http://YOUR_EC2_PUBLIC_IP:8080` from your browser using your actual public address.

The previous ECS Express/OIDC walkthrough is retained as an archived alternative in `AWS_CICD_GUIDE.md`; it is not the active deployment path.

AWS resources incur charges. A local browser URL does not establish that public deployment has occurred. For another container provider, expose port 8000, preserve both model files, and configure `/api/health`.

## API

- `GET /` — frontend.
- `GET /api/options` — supported property categories, limits, and example.
- `GET /api/health` — model readiness.
- `POST /api/predict` — validated JSON inputs and a real model estimate.

Example request:

```json
{
  "property_type": "flat",
  "sector": "sector 36",
  "bedRoom": 3,
  "bathroom": 2,
  "balcony": "2",
  "agePossession": "New Property",
  "built_up_area": 850,
  "servant room": 0,
  "store room": 0,
  "furnishing_type": "unfurnished",
  "luxury_category": "Low",
  "floor_category": "Low Floor"
}
```

The response includes `price_crore`, `price_rupees`, and `illustrative_range_crore`. The range is a fixed ±10% illustration, not a statistical prediction interval. Inputs outside the supported categories or numeric limits return JSON errors. No user-supplied pickle files are accepted.

Dependency versions match the environment used to load the saved model. Scikit-learn recommends matching the training environment when loading persisted models: [model persistence documentation](https://scikit-learn.org/stable/model_persistence.html). Production serving uses [Waitress](https://flask.palletsprojects.com/en/stable/deploying/waitress/) instead of Flask's development server.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests check the real prediction against direct pipeline inference and verify validation, JSON errors, and model readiness. Desktop and mobile browser screenshots, when generated, are saved in the ignored `artifacts/` directory.
