"""Verify startup, frontend, and a real prediction in a container or on AWS."""
import argparse
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request


def read_json(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {} if payload is None else {"Content-Type": "application/json"}
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=10) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--wait-seconds", type=int, default=30)
    args = parser.parse_args()
    if not args.base_url.strip():
        parser.error("The deployed endpoint is empty.")
    base = args.base_url.rstrip("/")
    if "://" not in base:
        base = "https://" + base
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme not in ["http", "https"] or not parsed.netloc:
        parser.error("Provide an HTTP or HTTPS application URL.")
    deadline = time.monotonic() + args.wait_seconds
    while True:
        try:
            if read_json(base + "/api/health")["status"] == "ready":
                break
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError("The model did not become ready within the startup allowance.")
        time.sleep(2)
    with urllib.request.urlopen(base, timeout=10) as response:
        if b"property-form" not in response.read():
            raise RuntimeError("The frontend was not served correctly.")
    example = read_json(base + "/api/options")["example"]
    prediction = read_json(base + "/api/predict", example)
    price = prediction["price_crore"]
    if not math.isfinite(price) or price <= 0:
        raise RuntimeError("The real model returned an invalid price.")
    if prediction["price_rupees"] != round(price * 10_000_000):
        raise RuntimeError("Price units are inconsistent.")
    example["built_up_area"] = -1
    try:
        read_json(base + "/api/predict", example)
    except urllib.error.HTTPError as error:
        if error.code != 400:
            raise RuntimeError("Invalid input did not produce a validation error.") from error
    else:
        raise RuntimeError("Invalid input was accepted.")
    print(f"Verified health, frontend, prediction ({price:.2f} crore), and input validation: {base}")


if __name__ == "__main__":
    main()
