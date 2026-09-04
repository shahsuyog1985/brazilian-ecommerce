-- DuckDB views over the raw Olist CSV files.
-- Run from the repository root after downloading the data.

CREATE OR REPLACE VIEW customers AS
SELECT * FROM read_csv_auto('data/raw/olist_customers_dataset.csv', header = true);

CREATE OR REPLACE VIEW geolocation AS
SELECT * FROM read_csv_auto('data/raw/olist_geolocation_dataset.csv', header = true);

CREATE OR REPLACE VIEW order_items AS
SELECT * FROM read_csv_auto('data/raw/olist_order_items_dataset.csv', header = true);

CREATE OR REPLACE VIEW order_payments AS
SELECT * FROM read_csv_auto('data/raw/olist_order_payments_dataset.csv', header = true);

CREATE OR REPLACE VIEW order_reviews AS
SELECT * FROM read_csv_auto('data/raw/olist_order_reviews_dataset.csv', header = true);

CREATE OR REPLACE VIEW orders AS
SELECT * FROM read_csv_auto('data/raw/olist_orders_dataset.csv', header = true);

CREATE OR REPLACE VIEW products AS
SELECT * FROM read_csv_auto('data/raw/olist_products_dataset.csv', header = true);

CREATE OR REPLACE VIEW sellers AS
SELECT * FROM read_csv_auto('data/raw/olist_sellers_dataset.csv', header = true);

CREATE OR REPLACE VIEW category_translation AS
SELECT * FROM read_csv_auto('data/raw/product_category_name_translation.csv', header = true);

-- One row per order prevents item × payment × review multiplication.
CREATE OR REPLACE VIEW order_item_summary AS
SELECT
    order_id,
    COUNT(*) AS item_count,
    SUM(price) AS item_revenue,
    SUM(freight_value) AS freight_value
FROM order_items
GROUP BY order_id;

CREATE OR REPLACE VIEW order_payment_summary AS
SELECT
    order_id,
    COUNT(*) AS payment_records,
    SUM(payment_value) AS payment_value
FROM order_payments
GROUP BY order_id;

CREATE OR REPLACE VIEW order_review_summary AS
SELECT
    order_id,
    AVG(review_score) AS review_score
FROM order_reviews
GROUP BY order_id;

CREATE OR REPLACE VIEW order_facts AS
SELECT
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    i.item_count,
    i.item_revenue,
    i.freight_value,
    p.payment_value,
    r.review_score,
    date_diff('second', o.order_purchase_timestamp, o.order_delivered_customer_date) / 86400.0 AS delivery_days,
    date_diff('second', o.order_estimated_delivery_date, o.order_delivered_customer_date) / 86400.0 AS delivery_delay_days,
    o.order_delivered_customer_date <= o.order_estimated_delivery_date AS arrived_on_time
FROM orders o
LEFT JOIN customers c USING (customer_id)
LEFT JOIN order_item_summary i USING (order_id)
LEFT JOIN order_payment_summary p USING (order_id)
LEFT JOIN order_review_summary r USING (order_id);
