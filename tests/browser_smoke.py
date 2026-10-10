"""Run against python app.py; requires Playwright and a Chromium/Edge browser."""
from pathlib import Path
import sys

from playwright.sync_api import expect, sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)

with sync_playwright() as playwright:
    launch_options = {"headless": True}
    if not Path(playwright.chromium.executable_path).exists():
        launch_options["channel"] = "msedge"
    browser = playwright.chromium.launch(**launch_options)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:8000", wait_until="networkidle")
    expect(page.get_by_role("button", name="Load example")).to_be_enabled()
    page.get_by_role("button", name="Load example").click()
    page.get_by_role("button", name="Estimate property price").click()
    expect(page.locator("#prediction-result")).to_be_visible()
    expect(page.locator("#price-value")).to_have_text("₹0.78 Cr")
    print("Desktop prediction:", page.locator("#price-value").inner_text())
    page.evaluate("window.scrollTo(0, 0)")
    page.screenshot(path=str(ARTIFACTS / "frontend-desktop.png"), full_page=True)

    page.get_by_label("Built-up area", exact=False).fill("1000")
    expect(page.locator("#prediction-result")).to_be_hidden()
    page.get_by_label("Built-up area", exact=False).fill("-1")
    page.get_by_role("button", name="Estimate property price").click()
    assert not page.get_by_label("Built-up area", exact=False).evaluate("element => element.validity.valid")
    print("Stale result and invalid area checks passed")

    page.get_by_role("button", name="Load example").click()
    page.route("**/api/predict", lambda route: route.fulfill(status=503, content_type="application/json", body='{"error":"Please try again later."}'))
    page.get_by_role("button", name="Estimate property price").click()
    expect(page.get_by_role("alert")).to_have_text("Please try again later.")
    expect(page.get_by_role("button", name="Estimate property price")).to_be_enabled()
    page.unroute("**/api/predict")
    page.get_by_role("button", name="Estimate property price").click()
    expect(page.locator("#prediction-result")).to_be_visible()
    print("API error and recovery checks passed")

    for width in [320, 390, 768, 1440]:
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), f"Horizontal overflow at {width}px"
    page.set_viewport_size({"width": 390, "height": 844})
    page.screenshot(path=str(ARTIFACTS / "frontend-mobile.png"), full_page=True)
    print("Responsive widths passed: 320, 390, 768, 1440px")
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.evaluate("document.documentElement.style.fontSize = '32px'")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Horizontal overflow at 200% text size"
    print("200% text-size layout passed")

    unavailable = browser.new_page()
    unavailable.route("**/api/options", lambda route: route.fulfill(status=503, content_type="application/json", body='{"error":"Service unavailable."}'))
    unavailable.goto("http://127.0.0.1:8000")
    expect(unavailable.get_by_role("status")).to_contain_text("Service unavailable.")
    expect(unavailable.get_by_role("button", name="Estimate property price")).to_be_disabled()
    print("Unavailable service state passed")
    assert not errors, errors
    print("No JavaScript exceptions")
    browser.close()
