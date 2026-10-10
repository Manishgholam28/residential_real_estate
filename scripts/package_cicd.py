"""Package only the source needed for GitHub CI and CloudShell setup."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
files = [
    "app.py", "model_service.py", "train_model.py", "requirements.txt",
    "requirements-ci.txt", "Dockerfile", ".dockerignore", ".gitignore",
    ".gitattributes", "README.md", "AWS_CICD_GUIDE.md", "DEPLOYMENT.md",
    "gurgaon_properties_missing_value_imputation.csv",
]
for folder in [".github/workflows", "infra", "scripts", "templates", "static", "tests"]:
    files.extend(str(path.relative_to(ROOT)) for path in (ROOT / folder).rglob("*")
                 if path.is_file() and "__pycache__" not in path.parts)

with ZipFile(ROOT / "aws-cicd-source.zip", "w", compression=ZIP_DEFLATED) as bundle:
    for name in sorted(set(files)):
        data = (ROOT / name).read_bytes()
        # Shell and workflow files must stay readable on Linux when uploaded as a zip.
        if Path(name).suffix in [".sh", ".yml", ".yaml"]:
            data = data.replace(b"\r\n", b"\n")
        bundle.writestr(Path(name).as_posix(), data)

print("Created aws-cicd-source.zip without saved models, credentials, or notebooks.")
