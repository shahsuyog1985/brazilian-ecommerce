# Advanced analysis and modeling

## Customer behavior

RFM segmentation groups 96,096 customers without publishing customer
identifiers. The largest group is **At risk** with 22,975 customers, while
15,376 customers fall into the **Champions** segment. Because repeat purchasing
is rare, frequency scores have less separation than recency and monetary scores.

Monthly cohort retention is available in
[`cohort_retention.csv`](reports/advanced/cohort_retention.csv). The results
reinforce the main finding that most customers appear only once.

## Seller and logistics performance

The seller scorecard ranks sellers by delivered item revenue and includes
orders, units, freight burden, average review, and late-delivery rate. Seller
IDs are replaced by revenue ranks in the published output. The logistics report
separates same-state and cross-state fulfillment as a simple distance proxy.

- [`seller_scorecard.csv`](reports/advanced/seller_scorecard.csv)
- [`logistics_routes.csv`](reports/advanced/logistics_routes.csv)

## Statistical relationships

Delivery delay has a Spearman correlation of **−0.176** with review score across
95,824 delivered orders with complete data. Freight and review score have a
weaker correlation of **−0.087**. The large sample makes even small effects
statistically significant, so effect size matters more than the p-value.

These tests are observational and do not establish causality.

## Predictive models

| Target | Holdout result | Interpretation |
|---|---:|---|
| Late delivery | ROC AUC 0.616 | Limited ranking signal from purchase-time attributes |
| Low review | ROC AUC 0.606 | Limited early-warning signal without post-purchase outcomes |
| Repeat purchase | ROC AUC 0.552 | First-order attributes alone are only slightly informative |
| Freight cost | MAE R$6.00; R² 0.548 | Product attributes explain part of freight variation |

The modest classification results are findings rather than failures: the
available purchase-time fields do not support confident individual predictions.
Production work should add richer features, use time-based validation, calibrate
probabilities, and monitor drift.

Detailed outputs:

- [`model_metrics.csv`](reports/advanced/model_metrics.csv)
- [`freight_feature_importance.csv`](reports/advanced/freight_feature_importance.csv)
- [`statistical_tests.csv`](reports/advanced/statistical_tests.csv)
- [`customer_segments.csv`](reports/advanced/customer_segments.csv)

## Reproduce

```powershell
python -m pip install -r requirements.txt
python scripts/download_data.py
python analysis/analyze.py
python analysis/advanced_analysis.py
streamlit run dashboard/app.py
```
