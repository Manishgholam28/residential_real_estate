"""Print only OIDC subject metadata, never the usable token or credentials."""
import base64
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request


def main():
    endpoint = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    separator = "&" if "?" in endpoint else "?"
    endpoint += separator + urllib.parse.urlencode({"audience": "sts.amazonaws.com"})
    request = urllib.request.Request(endpoint, headers={
        "Authorization": "Bearer " + os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        token = json.load(response)["value"]
    # Decode locally to display the subject; AWS will verify the token during login.
    part = token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    subject = claims["sub"]
    if not subject.endswith(":ref:refs/heads/main"):
        raise RuntimeError("Run this workflow on main without a GitHub environment.")
    print("AWS OIDC subject:", subject)
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as file:
        file.write("## Copy this exact subject into AWS setup\n\n")
        file.write(f"`{subject}`\n\n")
        file.write("This value identifies the repository and main branch. It is not a password.\n")


if __name__ == "__main__":
    main()
