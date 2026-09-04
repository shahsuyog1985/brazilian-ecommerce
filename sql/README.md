# SQL analysis

The SQL workflow uses [DuckDB](https://duckdb.org/) so it can query the source
CSV files directly without a database server.

## Run

From the repository root:

```powershell
duckdb olist.duckdb ".read sql/01_create_views.sql" ".read sql/02_analysis.sql"
```

The first script creates raw-data views and order-grain summary views. The
second contains eleven analyses:

1. Headline KPIs
2. Monthly order and payment trends
3. Product-category performance
4. Customer-state performance
5. Repeat-customer frequency
6. Monthly cohort retention
7. Delivery performance by state
8. Delivery timing and review scores
9. Payment-method mix
10. Seller concentration
11. Data-quality reconciliation

## Grain and join safety

`order_facts` contains one row per order. Items, payments, and reviews are
aggregated before joining, preventing many-to-many multiplication. Queries that
need product or seller detail use the item grain explicitly.
