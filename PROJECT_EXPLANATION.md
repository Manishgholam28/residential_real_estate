# Project explanation guide

This guide is based on the Python files, CSV datasets, notebook code, and saved notebook outputs in this folder. The models were not retrained for this review. Use the first-person script only for work you personally performed; adjust your contribution statement for team or tutorial-based work.

CI/CD update: `.github/workflows/ci-cd.yml` now defines model rebuilding, API checks, container checks, and deployment to ECR/ECS Express Mode. The AWS bootstrap and first-run steps are in `AWS_CICD_GUIDE.md`. These files do not establish that a GitHub run or live AWS deployment has occurred; demonstrate the actual successful run and URL before claiming that.

## Two-minute presentation script

“I worked on a Gurgaon Real Estate Price Prediction project. Its objective was to estimate residential property listing prices from property attributes and explore the factors associated with price differences.

The project uses flat and independent-house listing data sourced from 99acres. The raw files contain 3,017 flat listings and 1,044 house listings. After initial cleaning, the combined dataset contains 3,961 records, and the final modeling dataset contains 3,554 properties.

During preprocessing, I standardized prices into crores, extracted and normalized sector information, converted area measurements into square feet, and cleaned fields such as bedrooms, bathrooms, balconies, and possession age. I treated suspicious values and handled missing information using area relationships, median-based values, and group-based modes.

For feature engineering, I extracted indicators for additional rooms, used K-Means with three clusters to categorize furnishing information, and calculated an amenity-based luxury score. I then converted luxury scores and floor numbers into categories. The final model uses 12 input features.

I explored the data using univariate and multivariate analysis and compared regression models including Linear Regression, Decision Trees, Random Forest, Extra Trees, Gradient Boosting, and XGBoost. I applied a log transformation to property prices and evaluated the experiments using ten-fold cross-validation R² and a separate test-set MAE calculated in the original price units.

For the prediction application, I used a Scikit-learn pipeline containing numerical scaling, categorical encoding, and a Random Forest regressor with 500 trees. I saved the pipeline and input dataset using pickle. The current interface uses HTML, CSS, and JavaScript connected to a Flask prediction API. Users enter property details, and the application returns an estimated price in crores. Docker packaging is prepared; public cloud deployment has not yet been completed.

The repository also contains notebook-based geographic visualizations, price-factor analysis, and a content-based property recommendation prototype. These are separate analytical components; the current web application exposes price prediction.”

## Explain the project in this order

| Stage | What to explain | Main files |
| --- | --- | --- |
| Problem | Estimate Gurgaon residential listing prices from property attributes. | `app.py` |
| Data | Use separate flat and house CSVs with 99acres listing links. The scraping implementation is not present in this folder. | `flats.csv`, `houses.csv` |
| Initial cleaning | Normalize prices, society names, room counts, balconies, and floor details; merge cleaned data. | `data-preprocessing-flats.ipynb`, `data-preprocessing-houses.ipynb`, `merge-flats-and-house.ipynb` |
| Location cleaning | Extract sectors from property names and normalize locality labels. | `data-preprocessing-level-2.ipynb` |
| Feature engineering | Extract area types and additional rooms, cluster furnishing details, and calculate luxury scores. | `feature-engineering.ipynb` |
| EDA and data quality | Examine distributions and relationships; investigate outliers and impute missing values. | `eda-univariate-analysis.ipynb`, `eda-multivariate-analysis.ipynb`, `outlier-treatment.ipynb`, `missing-value-imputation.ipynb` |
| Feature selection | Compare correlations and several importance methods; build luxury and floor categories and reduce the inputs. | `feature-selection.ipynb` |
| Model experiments | Compare algorithms and encoding approaches; explore PCA, target encoding, and hyperparameter tuning. | `model-selection.ipynb` |
| Training and application | Fit and save the 500-tree Random Forest pipeline; serve predictions through Flask and an HTML/CSS/JavaScript interface. | `train_model.py`, `app.py`, `model_service.py`, `templates/index.html`, `static/app.js` |
| Additional analysis | Explore sector maps, price relationships, regression coefficients, and similar-property recommendations. | `data-visualization.ipynb`, `insights-module.ipynb`, `recommender-system.ipynb` |

## Numbers you can quote

| Item | Verified value |
| --- | --- |
| Raw flat listings | 3,017 |
| Raw house listings | 1,044 |
| Combined records after initial cleaning | 3,961 |
| Final modeling records | 3,554 |
| Final input features | 12 |
| Target | Property listing price in crores |
| Target transformation | `np.log1p(price)` |
| Inverse transformation at prediction | `np.expm1(prediction)` |
| Notebook validation | Ten-fold cross-validation for R²; 80:20 train/test split for MAE |
| Random Forest used by the training script | 500 trees, `random_state=42` |

The 12 inputs are property type, sector, bedrooms, bathrooms, balconies, age/possession, built-up area, servant room, store room, furnishing type, luxury category, and floor category.

### Report model results accurately

The following values are saved historical outputs from `model-selection.ipynb`, not results from a new evaluation of the current pickle file:

| Experiment | Mean cross-validation R² on log prices | Test MAE in crores |
| --- | --- | --- |
| Random Forest with ordinal encoding | 0.8803 | 0.5299 |
| Random Forest in the one-hot encoding comparison | 0.8911 | 0.5006 |
| Random Forest with sector target encoding | 0.9005 | 0.4536 |
| Tuned Random Forest with sector target encoding | Best grid-search R²: 0.9024 | Not reported for this tuned estimator |

The exported application pipeline uses ordinal encoding plus one-hot encoding of sector and possession age, with 500 trees. It does not use the tuned target-encoding estimator. Its exact validation metrics are not reported in the export section or `train_model.py`.

If asked about results, say: “One Random Forest experiment achieved approximately 0.90 cross-validation R² on log-transformed prices, with test MAE of approximately 0.454 crore, or ₹45.36 lakh. The application uses a separately exported Random Forest configuration.”

Do not describe R² as “90% prediction accuracy.” Also, Random Forest did not lead every comparison: Extra Trees had lower MAE in the one-hot comparison, while Random Forest had the lowest MAE in the target-encoding comparison.

## Questions to prepare for

### Why use log transformation?

Property prices have a long upper tail. `log1p` compresses the price range so expensive listings have less influence on the regression objective. Predictions are converted back with `expm1`. The notebook's R² is measured on log prices; its MAE is measured after converting back to crores.

### Why Random Forest?

Random Forest combines many decision trees and can represent nonlinear relationships and interactions between features. It performed well in the experiments and is the model used in the export code. Describe this as a practical choice supported by the comparisons; the code does not document a formal tradeoff study against every alternative.

### How did you handle missing area values?

The notebook estimates built-up area using relationships with super built-up area and carpet area. The implemented formulas use approximately `super_built_up_area / 1.105` and `carpet_area / 0.9`, averaging the estimates when both are available. Other fields use approaches such as a median-derived floor value and grouped possession-age modes.

### What did K-Means do?

It grouped listings by furnishing-item counts after scaling, using three clusters. The resulting labels were interpreted as unfurnished, semifurnished, and furnished. K-Means was used for feature engineering, not for price prediction. Cluster numbers have no inherent meaning, so their interpretation needs inspection.

### What is the luxury score?

It is a weighted sum of available amenities, using manually assigned weights. The final categories are Low for scores below 50, Medium from 50 to below 150, and High from 150 through 175. These weights represent design judgments, not learned causal effects.

### How were floors categorized?

Low Floor covers floors 0–2, Mid Floor covers 3–10, and High Floor covers 11–51.

### Why use a pipeline?

The saved pipeline applies the same scaling and encoding at training and prediction time. It combines `ColumnTransformer` preprocessing with the regressor. Random Forest itself does not require numerical scaling, but the repository includes scaling in its shared preprocessing approach.

### What happens when a user clicks Predict Price?

The browser sends the 12 inputs as JSON to `/api/predict`. Flask validates their categories and numeric limits, then creates a one-row DataFrame in the saved model's column order. The pipeline transforms the inputs and predicts a log price. The API applies `expm1`, and the browser displays the estimate in crores and rupees.

### What does the displayed price range mean?

The app calculates 90% and 110% of the point prediction. This is a fixed ±10% display band, not a statistically validated confidence or prediction interval.

### How does the recommender work?

The recommendation notebook explores cosine similarity using TF-IDF representations of facilities, encoded property attributes, and location-related features. Its combined scoring function weights these three similarity matrices. It is a notebook prototype and is not connected to the current web app.

### Why remove price per square foot?

Price per square foot contains information closely tied to the price target. Including a price-derived feature can introduce target leakage, and a buyer may not know it when requesting a price estimate. The training script excludes it.

### What are the main limitations and future improvements?

The data represents Gurgaon listings rather than verified transaction prices. Several cleaning and feature-engineering steps are performed in notebooks before model validation; a stricter evaluation would fit learned preprocessing only within training folds. The exported 500-tree pipeline needs its own documented held-out evaluation. Future work could add data refreshes, validated uncertainty intervals, monitoring, and deployment infrastructure.

## Correct the original explanation

- The original frontend used Streamlit. The current frontend uses HTML/CSS/JavaScript with a Flask REST API and Waitress server.
- Say “R² and MAE” for the implemented model comparisons. MSE and RMSE calculations were not found in the notebook source code reviewed.
- Describe DVC, MLflow, and AWS deployment as future work unless you implemented them elsewhere and can demonstrate it. Docker packaging has now been added; creating and verifying a public deployment remains a separate step.
- Describe analytics and recommendations as notebook components. They are not exposed by the current app.
- Say “used listing data sourced from 99acres” unless you personally performed the collection and can explain the scraper. Listing URLs verify the source, but scraper code is absent.
- Avoid calling the current project a scalable production-ready platform. The verified implementation is a data science workflow with a Flask prediction application and deployment files; cloud operation and load testing have not been demonstrated.

## Suggested demonstration

1. Show the raw flat and house datasets and their original text fields.
2. Explain two concrete transformations: prices into crores and area text into square feet.
3. Show the final dataset and its 12 input columns.
4. Show a model comparison table and explain the units and validation method.
5. Show `train_model.py` and the saved pipeline artifacts.
6. Run `.\.venv\Scripts\python.exe app.py`, open `http://localhost:8000`, load the example, and explain the browser-to-API prediction flow.
7. Finish with one challenge you personally solved and one realistic improvement.
