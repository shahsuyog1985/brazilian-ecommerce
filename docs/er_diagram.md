# Entity-relationship diagram

```mermaid
erDiagram
    CUSTOMERS ||--o{ ORDERS : places
    ORDERS ||--|{ ORDER_ITEMS : contains
    ORDERS ||--o{ ORDER_PAYMENTS : paid_by
    ORDERS ||--o{ ORDER_REVIEWS : receives
    PRODUCTS ||--o{ ORDER_ITEMS : appears_in
    SELLERS ||--o{ ORDER_ITEMS : fulfills
    CATEGORY_TRANSLATION ||--o{ PRODUCTS : translates

    CUSTOMERS {
        string customer_id PK
        string customer_unique_id
        int customer_zip_code_prefix
        string customer_city
        string customer_state
    }
    ORDERS {
        string order_id PK
        string customer_id FK
        string order_status
        timestamp order_purchase_timestamp
        timestamp order_delivered_customer_date
        timestamp order_estimated_delivery_date
    }
    ORDER_ITEMS {
        string order_id FK
        int order_item_id
        string product_id FK
        string seller_id FK
        decimal price
        decimal freight_value
    }
    PRODUCTS {
        string product_id PK
        string product_category_name FK
        int product_weight_g
        int product_length_cm
        int product_height_cm
        int product_width_cm
    }
    SELLERS {
        string seller_id PK
        int seller_zip_code_prefix
        string seller_city
        string seller_state
    }
    ORDER_PAYMENTS {
        string order_id FK
        int payment_sequential
        string payment_type
        int payment_installments
        decimal payment_value
    }
    ORDER_REVIEWS {
        string review_id
        string order_id FK
        int review_score
        timestamp review_creation_date
    }
    CATEGORY_TRANSLATION {
        string product_category_name PK
        string product_category_name_english
    }
```

`customer_id` identifies the customer record attached to an order.
`customer_unique_id` should be used to count people and repeat purchases.
Geolocation is intentionally not joined directly because ZIP-prefix rows are
not unique; aggregate them to one coordinate per prefix before use.
