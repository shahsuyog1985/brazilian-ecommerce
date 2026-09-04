# Predictive modeling

The project includes four portfolio models in `analysis/advanced_analysis.py`:

| Target | Model | Evaluation | Intended use |
|---|---|---|---|
| Late delivery | Balanced logistic regression | Holdout ROC AUC | Flag orders with higher delay risk |
| Low review | Balanced logistic regression | Holdout ROC AUC | Identify orders needing service attention |
| Freight cost | Random-forest regression | Holdout MAE and R² | Estimate shipping cost from item attributes |
| Repeat purchase | Balanced logistic regression | Holdout ROC AUC | Demonstrate first-order propensity modeling |

These models are demonstrations, not production decision systems. They use a
random holdout from historical marketplace data, do not establish causality,
and may not generalize beyond the dataset period. A production version should
use time-based validation, probability calibration, drift monitoring, fairness
review, and features known at the intended scoring time.
