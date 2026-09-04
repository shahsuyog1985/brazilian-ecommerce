"""Build aggregate reports and charts for the Olist public dataset."""

from __future__ import annotations

import html
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
CHARTS = REPORTS / "charts"


def read(name: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(RAW / name, **kwargs)


def money(value: float) -> str:
    return f"R$ {value:,.0f}"


def pct(value: float) -> str:
    return f"{value:.1%}"


def svg_bar(
    labels: list[str], values: list[float], title: str, subtitle: str, path: Path,
    value_format=lambda x: f"{x:,.0f}", color: str = "#1f6f8b",
) -> None:
    width, row_h, left, right, top = 1000, 34, 260, 130, 92
    height = top + row_h * len(labels) + 38
    plot_w = width - left - right
    max_value = max(values) if values else 1
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#17212b}.title{font-size:24px;font-weight:700}.sub{font-size:14px;fill:#5b6773}.label{font-size:13px}.value{font-size:13px;font-weight:700}</style>',
        f'<text class="title" x="24" y="34">{html.escape(title)}</text>',
        f'<text class="sub" x="24" y="58">{html.escape(subtitle)}</text>',
    ]
    for i, (label, value) in enumerate(zip(labels, values)):
        y = top + i * row_h
        bar_w = plot_w * value / max_value
        parts += [
            f'<text class="label" x="{left - 12}" y="{y + 18}" text-anchor="end">{html.escape(str(label))}</text>',
            f'<rect x="{left}" y="{y + 4}" width="{bar_w:.1f}" height="20" rx="3" fill="{color}"/>',
            f'<text class="value" x="{left + bar_w + 8:.1f}" y="{y + 19}">{html.escape(value_format(value))}</text>',
        ]
    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def svg_line(months: list[str], values: list[float], title: str, subtitle: str, path: Path) -> None:
    width, height, left, right, top, bottom = 1100, 440, 82, 28, 90, 65
    plot_w, plot_h = width - left - right, height - top - bottom
    vmax = max(values) * 1.08
    points = []
    for i, value in enumerate(values):
        x = left + plot_w * i / max(1, len(values) - 1)
        y = top + plot_h * (1 - value / vmax)
        points.append((x, y))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#17212b}.title{font-size:24px;font-weight:700}.sub{font-size:14px;fill:#5b6773}.axis{font-size:12px;fill:#5b6773}</style>',
        f'<text class="title" x="24" y="34">{html.escape(title)}</text>',
        f'<text class="sub" x="24" y="58">{html.escape(subtitle)}</text>',
    ]
    for tick in range(5):
        value = vmax * tick / 4
        y = top + plot_h * (1 - tick / 4)
        parts += [
            f'<line x1="{left}" x2="{width-right}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e3e8ed"/>',
            f'<text class="axis" x="{left-10}" y="{y+4:.1f}" text-anchor="end">{value/1_000_000:.1f}M</text>',
        ]
    path_d = " ".join(("M" if i == 0 else "L") + f" {x:.1f} {y:.1f}" for i, (x, y) in enumerate(points))
    parts.append(f'<path d="{path_d}" fill="none" stroke="#d95f02" stroke-width="4"/>')
    for i, ((x, y), month) in enumerate(zip(points, months)):
        if i % 3 == 0 or i == len(months) - 1:
            parts.append(f'<text class="axis" x="{x:.1f}" y="{height-bottom+26}" text-anchor="middle">{html.escape(month)}</text>')
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#d95f02"/>')
    parts += [
        f'<line x1="{left}" x2="{left}" y1="{top}" y2="{top+plot_h}" stroke="#9aa5b1"/>',
        f'<line x1="{left}" x2="{width-right}" y1="{top+plot_h}" y2="{top+plot_h}" stroke="#9aa5b1"/>',
        '</svg>',
    ]
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    CHARTS.mkdir(exist_ok=True)

    orders = read(
        "olist_orders_dataset.csv",
        parse_dates=[
            "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
            "order_delivered_customer_date", "order_estimated_delivery_date",
        ],
    )
    customers = read("olist_customers_dataset.csv")
    items = read("olist_order_items_dataset.csv")
    payments = read("olist_order_payments_dataset.csv")
    reviews = read("olist_order_reviews_dataset.csv")
    products = read("olist_products_dataset.csv")
    translation = read("product_category_name_translation.csv")
    sellers = read("olist_sellers_dataset.csv")

    category_map = dict(zip(translation.product_category_name, translation.product_category_name_english))
    products["category"] = products.product_category_name.map(category_map).fillna(products.product_category_name).fillna("unknown")

    item_order = items.groupby("order_id", as_index=False).agg(
        item_revenue=("price", "sum"), freight=("freight_value", "sum"), item_count=("order_item_id", "count")
    )
    payment_order = payments.groupby("order_id", as_index=False).agg(
        payment_value=("payment_value", "sum"), payment_records=("payment_sequential", "count")
    )
    review_order = reviews.groupby("order_id", as_index=False).agg(review_score=("review_score", "mean"))
    order = (
        orders.merge(customers, on="customer_id", how="left", validate="many_to_one")
        .merge(item_order, on="order_id", how="left", validate="one_to_one")
        .merge(payment_order, on="order_id", how="left", validate="one_to_one")
        .merge(review_order, on="order_id", how="left", validate="one_to_one")
    )
    order["month"] = order.order_purchase_timestamp.dt.to_period("M").astype(str)
    order["delivery_days"] = (order.order_delivered_customer_date - order.order_purchase_timestamp).dt.total_seconds() / 86400
    order["delivery_delay_days"] = (order.order_delivered_customer_date - order.order_estimated_delivery_date).dt.total_seconds() / 86400
    order["on_time"] = order.delivery_delay_days.le(0)

    delivered = order[order.order_status.eq("delivered")].copy()
    paid = order[order.payment_value.notna()].copy()

    monthly = paid.groupby("month", as_index=False).agg(
        orders=("order_id", "nunique"), customers=("customer_unique_id", "nunique"),
        payment_value=("payment_value", "sum"), average_order_value=("payment_value", "mean"),
    )
    monthly.to_csv(REPORTS / "monthly_performance.csv", index=False)

    item_enriched = (
        items.merge(products[["product_id", "category"]], on="product_id", how="left", validate="many_to_one")
        .merge(orders[["order_id", "order_status"]], on="order_id", how="left", validate="many_to_one")
    )
    category = (
        item_enriched[item_enriched.order_status.eq("delivered")]
        .groupby("category", as_index=False)
        .agg(orders=("order_id", "nunique"), units=("order_item_id", "count"), item_revenue=("price", "sum"), freight=("freight_value", "sum"))
        .sort_values("item_revenue", ascending=False)
    )
    category["average_item_price"] = category.item_revenue / category.units
    category.to_csv(REPORTS / "category_performance.csv", index=False)

    state = paid.groupby("customer_state", as_index=False).agg(
        orders=("order_id", "nunique"), customers=("customer_unique_id", "nunique"), payment_value=("payment_value", "sum")
    ).sort_values("payment_value", ascending=False)
    state["average_order_value"] = state.payment_value / state.orders
    state.to_csv(REPORTS / "state_performance.csv", index=False)

    payment_mix = payments.groupby("payment_type", as_index=False).agg(
        transactions=("order_id", "count"), orders=("order_id", "nunique"), payment_value=("payment_value", "sum")
    ).sort_values("payment_value", ascending=False)
    payment_mix["value_share"] = payment_mix.payment_value / payment_mix.payment_value.sum()
    payment_mix.to_csv(REPORTS / "payment_mix.csv", index=False)

    delivery_reviews = delivered.dropna(subset=["delivery_days", "review_score"]).assign(
        delivery_bucket=lambda d: pd.cut(
            d.delivery_delay_days,
            bins=[-np.inf, -7, -1e-9, 3, 7, np.inf],
            labels=["7+ days early", "1–6 days early", "0–3 days late", "4–7 days late", "8+ days late"],
        )
    ).groupby("delivery_bucket", observed=True, as_index=False).agg(
        orders=("order_id", "nunique"), average_review_score=("review_score", "mean")
    )
    delivery_reviews.to_csv(REPORTS / "delivery_review_relationship.csv", index=False)

    customer_orders = order.groupby("customer_unique_id").order_id.nunique()
    repeat_customers = int((customer_orders > 1).sum())
    total_customers = int(customer_orders.size)
    status_counts = orders.order_status.value_counts()
    delivered_with_timing = delivered.dropna(subset=["delivery_days", "delivery_delay_days"])
    dataset_start = orders.order_purchase_timestamp.min()
    dataset_end = orders.order_purchase_timestamp.max()
    full_months = monthly[(monthly.month >= "2017-01") & (monthly.month <= "2018-08")]
    first_6 = full_months.head(6).payment_value.sum()
    last_6 = full_months.tail(6).payment_value.sum()

    top_categories = category.head(12)
    svg_bar(
        top_categories.category.str.replace("_", " ").tolist(), top_categories.item_revenue.tolist(),
        "Top product categories by item revenue", "Delivered orders; excludes freight", CHARTS / "top_categories.svg",
        value_format=lambda x: f"R$ {x/1_000_000:.2f}M",
    )
    svg_bar(
        state.head(12).customer_state.tolist(), state.head(12).payment_value.tolist(),
        "Customer states by payment value", "All orders with recorded payments", CHARTS / "top_states.svg",
        value_format=lambda x: f"R$ {x/1_000_000:.2f}M", color="#4c78a8",
    )
    svg_bar(
        delivery_reviews.delivery_bucket.astype(str).tolist(), delivery_reviews.average_review_score.tolist(),
        "Delivery timing and customer reviews", "Mean review score by arrival relative to estimate", CHARTS / "delivery_reviews.svg",
        value_format=lambda x: f"{x:.2f} / 5", color="#59a14f",
    )
    svg_bar(
        payment_mix.payment_type.tolist(), payment_mix.payment_value.tolist(),
        "Payment value by method", "Recorded payments across all order statuses", CHARTS / "payment_methods.svg",
        value_format=lambda x: f"R$ {x/1_000_000:.2f}M", color="#9c755f",
    )
    svg_line(
        full_months.month.tolist(), full_months.payment_value.tolist(),
        "Monthly payment value", "Complete months from January 2017 through August 2018", CHARTS / "monthly_payment_value.svg",
    )

    report = f"""# Detailed analysis

## Executive summary

The dataset contains **{len(orders):,} orders** placed by **{total_customers:,} identifiable customers** from {dataset_start:%B %Y} through {dataset_end:%B %Y}. Recorded payments total **{money(payments.payment_value.sum())}**. Because the first and last calendar months are partial, trend comparisons use January 2017 through August 2018.

- Commerce scaled rapidly: payment value in the last six complete months was **{last_6 / first_6:.1f}×** the first six complete months.
- **{pct(status_counts.get('delivered', 0) / len(orders))}** of orders are marked delivered. Among delivered orders with complete timing data, **{pct(delivered_with_timing.on_time.mean())}** arrived by the estimated date.
- The median delivered order arrived in **{delivered_with_timing.delivery_days.median():.1f} days**; the 90th percentile was **{delivered_with_timing.delivery_days.quantile(.9):.1f} days**.
- Reviews are strongly associated with delivery performance: orders at least eight days late averaged **{delivery_reviews.loc[delivery_reviews.delivery_bucket.astype(str).eq('8+ days late'), 'average_review_score'].iloc[0]:.2f}/5**, versus **{delivery_reviews.loc[delivery_reviews.delivery_bucket.astype(str).eq('7+ days early'), 'average_review_score'].iloc[0]:.2f}/5** for orders at least seven days early.
- Repeat purchasing is limited: **{repeat_customers:,} customers ({pct(repeat_customers / total_customers)})** placed more than one order in the dataset.
- Credit cards account for **{pct(payment_mix.set_index('payment_type').loc['credit_card', 'value_share'])}** of payment value. The median credit-card installment count is **{payments.loc[payments.payment_type.eq('credit_card'), 'payment_installments'].median():.0f}**.
- The top category by delivered item revenue is **{top_categories.iloc[0].category.replace('_', ' ')}** at **{money(top_categories.iloc[0].item_revenue)}**. The top five categories contribute **{pct(category.head(5).item_revenue.sum() / category.item_revenue.sum())}** of delivered item revenue.
- São Paulo (SP) contributes **{pct(state.set_index('customer_state').loc['SP', 'payment_value'] / state.payment_value.sum())}** of recorded payment value, showing substantial geographic concentration.

## Sales trend

![Monthly payment value](reports/charts/monthly_payment_value.svg)

The curve shows sustained growth through the observed complete-month window, with seasonal volatility. Do not treat September and October 2018 as comparable full months because the dataset ends during October and operational timestamps extend beyond the purchase window.

The monthly detail is available in [`monthly_performance.csv`](reports/monthly_performance.csv).

## Product mix

![Top categories](reports/charts/top_categories.svg)

Category revenue uses delivered order items and excludes freight. Categories are translated to English when a mapping exists. Revenue concentration is meaningful but not extreme: the long tail still contributes most delivered item revenue outside the top five categories.

See [`category_performance.csv`](reports/category_performance.csv) for all categories, order counts, units, freight, and average item price.

## Geographic mix

![Top states](reports/charts/top_states.svg)

Payment value follows the largest consumer markets, led by São Paulo. State comparisons reflect customer location, not seller location, and do not control for population.

See [`state_performance.csv`](reports/state_performance.csv).

## Delivery and customer experience

![Delivery and reviews](reports/charts/delivery_reviews.svg)

Late delivery is associated with sharply lower ratings. This is observational rather than causal: product quality, seller quality, and service recovery may influence both timing and reviews.

See [`delivery_review_relationship.csv`](reports/delivery_review_relationship.csv).

## Payment behavior

![Payment methods](reports/charts/payment_methods.svg)

Credit cards dominate payment value, followed by boleto. Orders may have multiple payment records, so method-level transaction counts should not be added and interpreted as unique orders without deduplication.

See [`payment_mix.csv`](reports/payment_mix.csv).

## Methodology

- Orders are the base grain for order counts, delivery performance, customer counts, and average order value.
- Item revenue is the sum of `price`; freight is reported separately.
- Payment value is aggregated to one row per order before joining to prevent many-to-many inflation.
- Multiple reviews for an order are averaged before joining.
- A customer means `customer_unique_id`; `customer_id` is order-specific in this dataset.
- On-time means `order_delivered_customer_date <= order_estimated_delivery_date`.
- Trend charts exclude incomplete edge months and use January 2017 through August 2018.
- Raw rows and identifiers are not committed to Git. Generated reports contain aggregates only.

## Limitations

- The data covers orders placed on Olist in Brazil during the observed period; it is not a complete view of Brazilian e-commerce.
- Revenue figures are nominal Brazilian reais and are not adjusted for inflation, refunds, or marketplace fees.
- Recorded payment value and item-plus-freight totals can differ because of vouchers, multi-method payments, or data lifecycle effects.
- Review relationships are descriptive and should not be read as experimental causal estimates.
- The dataset includes partial first and last months and a small number of non-delivered orders.

## Reproduce

```powershell
python -m pip install kaggle pandas numpy
./scripts/download-data.ps1
python ./analysis/analyze.py
```

Source: [Brazilian E-Commerce Public Dataset by Olist on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). Check the Kaggle page for current license and usage terms.
"""
    (ROOT / "ANALYSIS.md").write_text(report, encoding="utf-8")
    print(f"Wrote analysis for {len(orders):,} orders to {REPORTS}")


if __name__ == "__main__":
    main()
