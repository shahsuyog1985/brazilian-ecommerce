"""Advanced customer, seller, logistics, statistical, and predictive analyses."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_absolute_error, r2_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "reports" / "advanced"
RANDOM_STATE = 42


def read(name: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(RAW / name, **kwargs)


def safe_auc(y_true, probability) -> float:
    return float(roc_auc_score(y_true, probability)) if pd.Series(y_true).nunique() == 2 else np.nan


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    orders = read(
        "olist_orders_dataset.csv",
        parse_dates=["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"],
    )
    customers = read("olist_customers_dataset.csv")
    items = read("olist_order_items_dataset.csv")
    products = read("olist_products_dataset.csv")
    sellers = read("olist_sellers_dataset.csv")
    reviews = read("olist_order_reviews_dataset.csv")
    payments = read("olist_order_payments_dataset.csv")

    item_orders = items.groupby("order_id", as_index=False).agg(
        item_revenue=("price", "sum"), freight=("freight_value", "sum"), item_count=("order_item_id", "count"),
        average_item_price=("price", "mean")
    )
    pay_orders = payments.groupby("order_id", as_index=False).agg(
        payment_value=("payment_value", "sum"), installments=("payment_installments", "max")
    )
    review_orders = reviews.groupby("order_id", as_index=False).review_score.mean()
    facts = (
        orders.merge(customers, on="customer_id", how="left")
        .merge(item_orders, on="order_id", how="left")
        .merge(pay_orders, on="order_id", how="left")
        .merge(review_orders, on="order_id", how="left")
    )
    facts["delivery_days"] = (facts.order_delivered_customer_date - facts.order_purchase_timestamp).dt.total_seconds() / 86400
    facts["delay_days"] = (facts.order_delivered_customer_date - facts.order_estimated_delivery_date).dt.total_seconds() / 86400
    facts["late"] = np.where(facts.delay_days.notna(), facts.delay_days.gt(0).astype(int), np.nan)
    facts["low_review"] = np.where(facts.review_score.notna(), facts.review_score.le(2).astype(int), np.nan)

    # RFM segments without exporting customer identifiers.
    reference_date = facts.order_purchase_timestamp.max() + pd.Timedelta(days=1)
    rfm = facts.groupby("customer_unique_id", as_index=False).agg(
        recency=("order_purchase_timestamp", lambda s: (reference_date - s.max()).days),
        frequency=("order_id", "nunique"), monetary=("payment_value", "sum")
    )
    rfm["r_score"] = pd.qcut(rfm.recency.rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["f_score"] = pd.qcut(rfm.frequency.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["m_score"] = pd.qcut(rfm.monetary.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    conditions = [
        (rfm.r_score >= 4) & (rfm.f_score >= 4),
        (rfm.r_score >= 3) & (rfm.f_score >= 3),
        (rfm.r_score >= 4) & (rfm.f_score <= 2),
        (rfm.r_score <= 2) & (rfm.f_score >= 3),
        (rfm.r_score <= 2) & (rfm.f_score <= 2),
    ]
    rfm["segment"] = np.select(conditions, ["Champions", "Loyal", "Promising", "At risk", "Hibernating"], default="Developing")
    segment_summary = rfm.groupby("segment", as_index=False).agg(
        customers=("customer_unique_id", "count"), median_recency_days=("recency", "median"),
        average_orders=("frequency", "mean"), average_customer_value=("monetary", "mean")
    ).sort_values("customers", ascending=False)
    segment_summary.to_csv(OUT / "customer_segments.csv", index=False)

    # Cohort retention.
    customer_months = facts[["customer_unique_id", "order_purchase_timestamp"]].dropna().assign(
        order_month=lambda d: d.order_purchase_timestamp.dt.to_period("M")
    ).drop_duplicates(["customer_unique_id", "order_month"])
    customer_months["cohort_month"] = customer_months.groupby("customer_unique_id").order_month.transform("min")
    customer_months["months_since_first"] = (
        customer_months.order_month.astype(int) - customer_months.cohort_month.astype(int)
    )
    cohorts = customer_months.groupby(["cohort_month", "months_since_first"]).customer_unique_id.nunique().rename("active_customers").reset_index()
    cohort_size = cohorts[cohorts.months_since_first.eq(0)].set_index("cohort_month").active_customers
    cohorts["cohort_size"] = cohorts.cohort_month.map(cohort_size)
    cohorts["retention_rate"] = cohorts.active_customers / cohorts.cohort_size
    cohorts[["cohort_month", "months_since_first", "active_customers", "cohort_size", "retention_rate"]].to_csv(OUT / "cohort_retention.csv", index=False)

    # Seller scorecard; sellers are ranked instead of exposing IDs.
    seller_items = items.merge(orders[["order_id", "order_status", "order_delivered_customer_date", "order_estimated_delivery_date"]], on="order_id").merge(review_orders, on="order_id", how="left")
    seller_items["late"] = seller_items.order_delivered_customer_date.gt(seller_items.order_estimated_delivery_date)
    seller_score = seller_items.groupby("seller_id", as_index=False).agg(
        orders=("order_id", "nunique"), units=("order_item_id", "count"), item_revenue=("price", "sum"),
        freight=("freight_value", "sum"), average_review=("review_score", "mean"), late_rate=("late", "mean")
    ).sort_values("item_revenue", ascending=False).reset_index(drop=True)
    seller_score.insert(0, "seller_rank", np.arange(1, len(seller_score) + 1))
    seller_score["freight_burden"] = seller_score.freight / seller_score.item_revenue
    seller_score.drop(columns="seller_id").to_csv(OUT / "seller_scorecard.csv", index=False)

    # Logistics by customer and seller state, with a same-state distance proxy.
    logistics = seller_items.merge(sellers[["seller_id", "seller_state"]], on="seller_id", how="left").merge(
        facts[["order_id", "customer_state", "delivery_days", "delay_days"]], on="order_id", how="left"
    )
    logistics["route"] = np.where(logistics.customer_state.eq(logistics.seller_state), "same state", "different state")
    logistics_summary = logistics.groupby("route", as_index=False).agg(
        order_items=("order_item_id", "count"), median_delivery_days=("delivery_days", "median"),
        p90_delivery_days=("delivery_days", lambda s: s.quantile(.9)), average_freight=("freight_value", "mean"),
        late_rate=("delay_days", lambda s: s.gt(0).mean())
    )
    logistics_summary.to_csv(OUT / "logistics_routes.csv", index=False)

    # Statistical associations; effect sizes are reported with p-values.
    stats_rows = []
    delivered = facts.query("order_status == 'delivered'").dropna(subset=["delay_days", "review_score"])
    rho, p_value = spearmanr(delivered.delay_days, delivered.review_score)
    stats_rows.append(("Delivery delay vs review", "Spearman rho", rho, p_value, len(delivered)))
    late_reviews = delivered.loc[delivered.delay_days.gt(0), "review_score"]
    ontime_reviews = delivered.loc[delivered.delay_days.le(0), "review_score"]
    statistic, p_value = mannwhitneyu(late_reviews, ontime_reviews, alternative="two-sided")
    stats_rows.append(("Late vs on-time review", "Mann-Whitney U", statistic, p_value, len(delivered)))
    rho, p_value = spearmanr(facts.dropna(subset=["freight", "review_score"]).freight, facts.dropna(subset=["freight", "review_score"]).review_score)
    stats_rows.append(("Freight vs review", "Spearman rho", rho, p_value, int(facts[["freight", "review_score"]].dropna().shape[0])))
    pd.DataFrame(stats_rows, columns=["analysis", "test", "statistic", "p_value", "observations"]).to_csv(OUT / "statistical_tests.csv", index=False)

    # Predictive models use an out-of-sample holdout. Results describe this dataset only.
    features = ["item_revenue", "freight", "item_count", "installments", "customer_state"]
    numeric = features[:-1]
    categorical = ["customer_state"]
    prep = ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
    ])
    model_rows = []
    for target, name in [("late", "Late delivery"), ("low_review", "Low review")]:
        model_data = facts.dropna(subset=[target]).copy()
        x_train, x_test, y_train, y_test = train_test_split(
            model_data[features], model_data[target], test_size=.25, random_state=RANDOM_STATE, stratify=model_data[target]
        )
        pipeline = Pipeline([("prepare", prep), ("model", LogisticRegression(max_iter=1000, class_weight="balanced"))])
        pipeline.fit(x_train, y_train)
        probability = pipeline.predict_proba(x_test)[:, 1]
        model_rows.append((name, "Logistic regression", "ROC AUC", safe_auc(y_test, probability), len(x_train), len(x_test)))

    customer_frequency = facts.groupby("customer_unique_id").order_id.nunique()
    first_orders = facts.sort_values("order_purchase_timestamp").drop_duplicates("customer_unique_id").copy()
    first_orders["repeat_customer"] = first_orders.customer_unique_id.map(customer_frequency).gt(1).astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        first_orders[features], first_orders.repeat_customer, test_size=.25,
        random_state=RANDOM_STATE, stratify=first_orders.repeat_customer
    )
    repeat_pipeline = Pipeline([("prepare", prep), ("model", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    repeat_pipeline.fit(x_train, y_train)
    probability = repeat_pipeline.predict_proba(x_test)[:, 1]
    model_rows.append(("Repeat purchase", "Logistic regression", "ROC AUC", safe_auc(y_test, probability), len(x_train), len(x_test)))

    freight_data = items.merge(products, on="product_id", how="left").dropna(subset=["freight_value", "price"])
    freight_features = ["price", "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"]
    x_train, x_test, y_train, y_test = train_test_split(
        freight_data[freight_features], freight_data.freight_value, test_size=.25, random_state=RANDOM_STATE
    )
    reg = Pipeline([("impute", SimpleImputer(strategy="median")), ("model", RandomForestRegressor(n_estimators=100, min_samples_leaf=5, n_jobs=-1, random_state=RANDOM_STATE))])
    reg.fit(x_train, y_train)
    prediction = reg.predict(x_test)
    model_rows += [
        ("Freight cost", "Random forest", "MAE", mean_absolute_error(y_test, prediction), len(x_train), len(x_test)),
        ("Freight cost", "Random forest", "R²", r2_score(y_test, prediction), len(x_train), len(x_test)),
    ]
    pd.DataFrame(model_rows, columns=["target", "model", "metric", "value", "training_rows", "test_rows"]).to_csv(OUT / "model_metrics.csv", index=False)

    importances = pd.DataFrame({"feature": freight_features, "importance": reg.named_steps["model"].feature_importances_}).sort_values("importance", ascending=False)
    importances.to_csv(OUT / "freight_feature_importance.csv", index=False)
    print(f"Advanced outputs written to {OUT}")


if __name__ == "__main__":
    main()
