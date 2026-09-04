-- Detailed SQL analysis for the Olist Brazilian e-commerce dataset.
-- Execute 01_create_views.sql first.

-- 1. Headline KPIs at the order grain.
SELECT
    COUNT(*) AS orders,
    COUNT(DISTINCT customer_unique_id) AS customers,
    MIN(order_purchase_timestamp)::DATE AS first_purchase_date,
    MAX(order_purchase_timestamp)::DATE AS last_purchase_date,
    ROUND(SUM(payment_value), 2) AS recorded_payment_value,
    ROUND(AVG(payment_value), 2) AS average_order_value,
    ROUND(100.0 * COUNT_IF(order_status = 'delivered') / COUNT(*), 2) AS delivered_order_pct
FROM order_facts;

-- 2. Complete-month order and payment trend.
SELECT
    date_trunc('month', order_purchase_timestamp)::DATE AS purchase_month,
    COUNT(*) AS orders,
    COUNT(DISTINCT customer_unique_id) AS customers,
    ROUND(SUM(payment_value), 2) AS payment_value,
    ROUND(AVG(payment_value), 2) AS average_order_value,
    ROUND(
        100.0 * (SUM(payment_value) / LAG(SUM(payment_value)) OVER (ORDER BY purchase_month) - 1),
        2
    ) AS payment_value_mom_pct
FROM order_facts
WHERE order_purchase_timestamp >= DATE '2017-01-01'
  AND order_purchase_timestamp < DATE '2018-09-01'
GROUP BY purchase_month
ORDER BY purchase_month;

-- 3. Delivered item revenue by translated product category.
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    COUNT(DISTINCT i.order_id) AS orders,
    COUNT(*) AS units,
    ROUND(SUM(i.price), 2) AS item_revenue,
    ROUND(SUM(i.freight_value), 2) AS freight_value,
    ROUND(AVG(i.price), 2) AS average_item_price
FROM order_items i
JOIN orders o USING (order_id)
LEFT JOIN products p USING (product_id)
LEFT JOIN category_translation t USING (product_category_name)
WHERE o.order_status = 'delivered'
GROUP BY category
ORDER BY item_revenue DESC;

-- 4. Customer-state performance.
SELECT
    customer_state,
    COUNT(*) AS orders,
    COUNT(DISTINCT customer_unique_id) AS customers,
    ROUND(SUM(payment_value), 2) AS payment_value,
    ROUND(AVG(payment_value), 2) AS average_order_value,
    ROUND(100.0 * SUM(payment_value) / SUM(SUM(payment_value)) OVER (), 2) AS payment_value_share_pct
FROM order_facts
WHERE payment_value IS NOT NULL
GROUP BY customer_state
ORDER BY payment_value DESC;

-- 5. Repeat-customer distribution. customer_unique_id represents a person;
-- customer_id is specific to an order/address record.
WITH customer_orders AS (
    SELECT customer_unique_id, COUNT(DISTINCT order_id) AS order_count
    FROM order_facts
    WHERE customer_unique_id IS NOT NULL
    GROUP BY customer_unique_id
)
SELECT
    CASE
        WHEN order_count = 1 THEN '1 order'
        WHEN order_count = 2 THEN '2 orders'
        WHEN order_count = 3 THEN '3 orders'
        ELSE '4+ orders'
    END AS order_frequency,
    COUNT(*) AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS customer_share_pct
FROM customer_orders
GROUP BY order_frequency
ORDER BY MIN(order_count);

-- 6. Cohort retention by months since first purchase.
WITH customer_months AS (
    SELECT DISTINCT
        customer_unique_id,
        date_trunc('month', order_purchase_timestamp)::DATE AS order_month
    FROM order_facts
    WHERE customer_unique_id IS NOT NULL
      AND order_purchase_timestamp >= DATE '2017-01-01'
      AND order_purchase_timestamp < DATE '2018-09-01'
),
cohorted AS (
    SELECT
        customer_unique_id,
        order_month,
        MIN(order_month) OVER (PARTITION BY customer_unique_id) AS cohort_month
    FROM customer_months
),
retention AS (
    SELECT
        cohort_month,
        date_diff('month', cohort_month, order_month) AS months_since_first_order,
        COUNT(DISTINCT customer_unique_id) AS active_customers
    FROM cohorted
    GROUP BY cohort_month, months_since_first_order
),
cohort_sizes AS (
    SELECT cohort_month, active_customers AS cohort_size
    FROM retention
    WHERE months_since_first_order = 0
)
SELECT
    r.cohort_month,
    r.months_since_first_order,
    r.active_customers,
    c.cohort_size,
    ROUND(100.0 * r.active_customers / c.cohort_size, 2) AS retention_pct
FROM retention r
JOIN cohort_sizes c USING (cohort_month)
ORDER BY r.cohort_month, r.months_since_first_order;

-- 7. Delivery speed and on-time rate by customer state.
SELECT
    customer_state,
    COUNT(*) AS delivered_orders,
    ROUND(MEDIAN(delivery_days), 2) AS median_delivery_days,
    ROUND(quantile_cont(delivery_days, 0.9), 2) AS p90_delivery_days,
    ROUND(100.0 * COUNT_IF(arrived_on_time) / COUNT(*), 2) AS on_time_pct,
    ROUND(AVG(review_score), 2) AS average_review_score
FROM order_facts
WHERE order_status = 'delivered'
  AND delivery_days IS NOT NULL
  AND delivery_delay_days IS NOT NULL
GROUP BY customer_state
ORDER BY on_time_pct, delivered_orders DESC;

-- 8. Delivery timing relationship with review scores.
WITH bucketed AS (
    SELECT
        CASE
            WHEN delivery_delay_days <= -7 THEN '7+ days early'
            WHEN delivery_delay_days <= 0 THEN '1–6 days early'
            WHEN delivery_delay_days <= 3 THEN '0–3 days late'
            WHEN delivery_delay_days <= 7 THEN '4–7 days late'
            ELSE '8+ days late'
        END AS delivery_bucket,
        CASE
            WHEN delivery_delay_days <= -7 THEN 1
            WHEN delivery_delay_days <= 0 THEN 2
            WHEN delivery_delay_days <= 3 THEN 3
            WHEN delivery_delay_days <= 7 THEN 4
            ELSE 5
        END AS bucket_order,
        review_score
    FROM order_facts
    WHERE order_status = 'delivered'
      AND delivery_delay_days IS NOT NULL
      AND review_score IS NOT NULL
)
SELECT
    delivery_bucket,
    COUNT(*) AS orders,
    ROUND(AVG(review_score), 2) AS average_review_score,
    ROUND(100.0 * COUNT_IF(review_score <= 2) / COUNT(*), 2) AS low_review_pct
FROM bucketed
GROUP BY delivery_bucket, bucket_order
ORDER BY bucket_order;

-- 9. Payment-method mix. One order can use more than one payment method.
SELECT
    payment_type,
    COUNT(*) AS payment_records,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(payment_value), 2) AS payment_value,
    ROUND(100.0 * SUM(payment_value) / SUM(SUM(payment_value)) OVER (), 2) AS payment_value_share_pct,
    ROUND(AVG(NULLIF(payment_installments, 0)), 2) AS average_installments
FROM order_payments
GROUP BY payment_type
ORDER BY payment_value DESC;

-- 10. Seller concentration and service outcomes.
WITH seller_orders AS (
    SELECT
        i.seller_id,
        COUNT(DISTINCT i.order_id) AS orders,
        SUM(i.price) AS item_revenue,
        AVG(r.review_score) AS average_review_score
    FROM order_items i
    JOIN orders o USING (order_id)
    LEFT JOIN order_review_summary r USING (order_id)
    WHERE o.order_status = 'delivered'
    GROUP BY i.seller_id
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY item_revenue DESC) AS revenue_rank
    FROM seller_orders
)
SELECT
    CASE
        WHEN revenue_rank <= 10 THEN 'Top 10'
        WHEN revenue_rank <= 100 THEN 'Ranks 11–100'
        ELSE 'All other sellers'
    END AS seller_group,
    COUNT(*) AS sellers,
    SUM(orders) AS seller_order_relationships,
    ROUND(SUM(item_revenue), 2) AS item_revenue,
    ROUND(100.0 * SUM(item_revenue) / SUM(SUM(item_revenue)) OVER (), 2) AS item_revenue_share_pct,
    ROUND(AVG(average_review_score), 2) AS unweighted_average_seller_review
FROM ranked
GROUP BY seller_group
ORDER BY MIN(revenue_rank);

-- 11. Data-quality reconciliation at distinct grains.
SELECT
    (SELECT COUNT(*) FROM orders) AS order_rows,
    (SELECT COUNT(DISTINCT order_id) FROM orders) AS distinct_orders,
    (SELECT COUNT(*) FROM order_items) AS item_rows,
    (SELECT COUNT(*) FROM order_payments) AS payment_rows,
    (SELECT COUNT(*) FROM order_reviews) AS review_rows,
    (SELECT COUNT(*) FROM products) AS product_rows,
    (SELECT COUNT(*) FROM sellers) AS seller_rows,
    (SELECT COUNT(*) FROM customers) AS customer_rows;
