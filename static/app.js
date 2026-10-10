"use strict";
const form = document.getElementById("property-form");
const fields = document.getElementById("property-fields");
const status = document.getElementById("service-status");
const errorMessage = document.getElementById("form-error");
const predictButton = document.getElementById("predict-button");
const exampleButton = document.getElementById("example-button");
const numericFields = ["bedRoom", "bathroom", "built_up_area", "servant room", "store room"];
let example;

function displayLabel(value) {
  const labels = {flat: "Flat", house: "Independent house", unfurnished: "Unfurnished", semifurnished: "Semi-furnished", furnished: "Furnished"};
  return labels[value] || value.charAt(0).toUpperCase() + value.slice(1);
}
async function readResponse(response) {
  let data;
  try { data = await response.json(); }
  catch { throw new Error("The service did not respond as expected. Please try again."); }
  if (!response.ok) throw new Error(data.error || "The prediction service is unavailable.");
  return data;
}
function clearResult() {
  document.getElementById("empty-result").hidden = false;
  document.getElementById("prediction-result").hidden = true;
  errorMessage.hidden = true;
}
async function initialize() {
  try {
    const options = await readResponse(await fetch("/api/options"));
    example = options.example;
    for (const [name, choices] of Object.entries(options.choices)) {
      const select = form.elements.namedItem(name);
      select.replaceChildren(...choices.map(value => new Option(displayLabel(value), value)));
    }
    for (const [name, limits] of Object.entries(options.limits)) {
      const input = form.elements.namedItem(name);
      if (input.tagName === "INPUT") { input.min = limits.min; input.max = limits.max; }
    }
    for (const [name, value] of Object.entries(example)) {
      if (!numericFields.includes(name)) form.elements.namedItem(name).value = String(value);
    }
    fields.disabled = false;
    exampleButton.disabled = false;
    status.hidden = true;
  } catch (error) {
    status.classList.add("error");
    status.textContent = error.message + " Refresh this page to retry.";
  }
}
exampleButton.addEventListener("click", () => {
  for (const [name, value] of Object.entries(example)) form.elements.namedItem(name).value = String(value);
  clearResult();
  form.elements.namedItem("property_type").focus();
});
form.addEventListener("input", clearResult);
form.addEventListener("change", clearResult);
form.addEventListener("submit", async event => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  errorMessage.hidden = true;
  const payload = Object.fromEntries(new FormData(form));
  for (const name of numericFields) payload[name] = Number(payload[name]);
  fields.disabled = true;
  exampleButton.disabled = true;
  predictButton.textContent = "Estimating your property…";
  form.setAttribute("aria-busy", "true");
  try {
    const result = await readResponse(await fetch("/api/predict", {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)
    }));
    const money = value => "₹" + value.toFixed(2) + " Cr";
    document.getElementById("price-value").textContent = money(result.price_crore);
    document.getElementById("price-rupees").textContent = new Intl.NumberFormat("en-IN", {style: "currency", currency: "INR", maximumFractionDigits: 0}).format(result.price_rupees);
    document.getElementById("range-value").textContent = money(result.illustrative_range_crore.low) + " – " + money(result.illustrative_range_crore.high);
    const property = result.property;
    document.getElementById("property-summary").textContent = `${property.bedRoom} bedroom ${property.property_type === "flat" ? "flat" : "house"} · ${displayLabel(property.sector)} · ${new Intl.NumberFormat("en-IN").format(property.built_up_area)} sqft · ${displayLabel(property.furnishing_type)}`;
    document.getElementById("empty-result").hidden = true;
    document.getElementById("prediction-result").hidden = false;
    if (window.matchMedia("(max-width: 850px)").matches) document.querySelector(".estimate-card").scrollIntoView({behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start"});
  } catch (error) {
    errorMessage.textContent = error.message;
    errorMessage.hidden = false;
  } finally {
    fields.disabled = false;
    exampleButton.disabled = false;
    predictButton.textContent = "Estimate property price";
    form.removeAttribute("aria-busy");
  }
});
initialize();
