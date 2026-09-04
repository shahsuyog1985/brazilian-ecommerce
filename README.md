# Brazilian E-Commerce Dataset

This repository provides a reproducible analysis of the
[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

Read the [detailed analysis](ANALYSIS.md) for sales growth, product mix,
geographic concentration, delivery performance, customer reviews, repeat
purchasing, and payment behavior. Aggregate CSV reports and charts are stored
under `reports/`.

A separate [DuckDB SQL workflow](sql/README.md) includes reusable views and
eleven documented analyses for KPIs, trends, cohorts, delivery, sellers, and
data-quality reconciliation.

The raw dataset is not stored in Git. Download it from Kaggle with the helper
script below, after installing and configuring the Kaggle CLI.

## Download

```powershell
python -m pip install kaggle
./scripts/download-data.ps1
python ./analysis/analyze.py
```

The files are extracted into `data/raw/`, which is intentionally excluded from
version control.

## Data source and terms

- Source: Olist on Kaggle
- Dataset: Brazilian E-Commerce Public Dataset by Olist
- Terms and license: see the dataset's Kaggle page before using or redistributing
  the data

This repository is not affiliated with or endorsed by Olist or Kaggle.
