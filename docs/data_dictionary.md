# Data dictionary

| Table | Grain | Primary key | Important fields | Analytical use |
|---|---|---|---|---|
| customers | One order-specific customer record | `customer_id` | `customer_unique_id`, city, state, ZIP prefix | Unique people and customer geography |
| orders | One order | `order_id` | Status and purchase, approval, carrier, delivery, estimate timestamps | Order counts, funnel status, delivery performance |
| order_items | One product line within an order | `order_id`, `order_item_id` | Product, seller, price, freight | Product, seller, and item revenue analysis |
| order_payments | One payment sequence per order | `order_id`, `payment_sequential` | Type, installments, value | Tender mix and recorded payment value |
| order_reviews | One submitted review record | `review_id` | Order, score, comment fields, dates | Customer experience |
| products | One product | `product_id` | Category, dimensions, weight, media counts | Category and freight features |
| sellers | One seller | `seller_id` | City, state, ZIP prefix | Seller performance and logistics routes |
| geolocation | Multiple coordinate observations per ZIP prefix | None | ZIP prefix, latitude, longitude, city, state | Approximate spatial analysis after aggregation |
| category_translation | One Portuguese category mapping | `product_category_name` | English category name | Readable category labels |

## Measures

| Measure | Definition |
|---|---|
| Orders | Distinct `order_id` at the order grain |
| Customers | Distinct `customer_unique_id` |
| Item revenue | Sum of `order_items.price`; excludes freight |
| Freight | Sum of `order_items.freight_value` |
| Recorded payment value | Sum of payments after aggregating payment rows to orders |
| On-time order | Customer delivery timestamp is on or before the estimated delivery timestamp |
| Repeat customer | `customer_unique_id` with more than one distinct order |
| Low review | Review score of 1 or 2 |

## Join cautions

- Aggregate items, payments, and reviews separately before joining them at the order grain.
- Do not count `customer_id` as a person.
- Do not directly join raw geolocation rows to customers or sellers.
- State whether revenue means item revenue or recorded payment value.
