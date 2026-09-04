# Brazilian E-Commerce Dataset

This repository provides a reproducible starting point for working with the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

The raw dataset is not stored in Git. Download it from Kaggle with the helper script below, after installing and configuring the Kaggle CLI.

## Download

```powershell
python -m pip install kaggle
./scripts/download-data.ps1
```

The files are extracted into `data/raw/`, which is intentionally excluded from version control.

## Data source and terms

- Source: Olist on Kaggle
- Dataset: Brazilian E-Commerce Public Dataset by Olist
- Terms and license: see the dataset's Kaggle page before using or redistributing the data

This repository is not affiliated with or endorsed by Olist or Kaggle.
