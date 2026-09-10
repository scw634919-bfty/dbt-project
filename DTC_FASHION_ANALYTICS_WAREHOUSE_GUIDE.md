# DTC Fashion Analytics Warehouse with dbt

This guide is a step-by-step plan for building a Direct-to-Consumer (DTC) fashion analytics warehouse with dbt and SQL using the CSV files in `dataset/`.

The goal is to turn raw marketplace data into trustworthy analytics for:

- Revenue and order performance
- Product and category performance
- Customer behavior and retention
- Seller performance
- Delivery performance
- Payment and review analysis

This document describes what to build and why. It does not implement the dbt project for you.

## 1. Recommended Project Structure

```text
dbt-project/
|-- dataset/
|   |-- olist_customers_dataset.csv
|   |-- olist_geolocation_dataset.csv
|   |-- olist_order_items_dataset.csv
|   |-- olist_order_payments_dataset.csv
|   |-- olist_order_reviews_dataset.csv
|   |-- olist_orders_dataset.csv
|   |-- olist_products_dataset.csv
|   |-- olist_sellers_dataset.csv
|   `-- product_category_name_translation.csv
|
|-- models/
|   |-- staging/
|   |   |-- stg_olist__customers.sql
|   |   |-- stg_olist__geolocation.sql
|   |   |-- stg_olist__order_items.sql
|   |   |-- stg_olist__order_payments.sql
|   |   |-- stg_olist__order_reviews.sql
|   |   |-- stg_olist__orders.sql
|   |   |-- stg_olist__products.sql
|   |   |-- stg_olist__sellers.sql
|   |   |-- stg_olist__category_translation.sql
|   |   `-- schema.yml
|   |
|   |-- intermediate/
|   |   |-- int_olist__order_payments.sql
|   |   |-- int_olist__order_reviews.sql
|   |   |-- int_olist__order_items_enriched.sql
|   |   |-- int_olist__orders_enriched.sql
|   |   `-- schema.yml
|   |
|   `-- marts/
|       |-- core/
|       |   |-- fct_orders.sql
|       |   |-- fct_order_items.sql
|       |   |-- dim_customers.sql
|       |   |-- dim_products.sql
|       |   |-- dim_sellers.sql
|       |   `-- schema.yml
|       |
|       |-- finance/
|       |   |-- fct_order_payments.sql
|       |   |-- finance_daily_metrics.sql
|       |   `-- schema.yml
|       |
|       |-- customer/
|       |   |-- customer_order_summary.sql
|       |   |-- customer_retention.sql
|       |   `-- schema.yml
|       |
|       |-- product/
|       |   |-- product_performance.sql
|       |   |-- category_performance.sql
|       |   `-- schema.yml
|       |
|       `-- operations/
|           |-- delivery_performance.sql
|           |-- seller_performance.sql
|           |-- review_performance.sql
|           `-- schema.yml
|
|-- analyses/
|   `-- exploratory_queries.sql
|-- macros/
|   `-- reusable_sql_macros.sql
|-- snapshots/
|   `-- optional_snapshot_models.sql
|-- tests/
|   `-- custom_data_tests.sql
|-- dbt_project.yml
|-- profiles.yml              # Usually stored outside the project directory
|-- packages.yml               # Optional, only if packages are needed
`-- README.md
```

The directories have been created in this workspace. Create the SQL, YAML, and configuration files gradually as you work through the phases below.

## 2. Understand the Dataset Before Writing SQL

Start by understanding the grain and keys of every CSV. Do not join tables until you know whether a table has one row per order, item, payment, review, or customer.

| CSV | Expected grain | Important keys | Main use |
|---|---|---|---|
| `olist_orders_dataset.csv` | One row per order | `order_id`, `customer_id` | Order lifecycle and delivery |
| `olist_order_items_dataset.csv` | One row per item within an order | `order_id`, `order_item_id`, `product_id`, `seller_id` | Product sales and freight |
| `olist_order_payments_dataset.csv` | One row per payment installment or payment record | `order_id`, `payment_sequential` | Payment totals and methods |
| `olist_order_reviews_dataset.csv` | One row per review record | `review_id`, `order_id` | Satisfaction and review timing |
| `olist_customers_dataset.csv` | One row per customer-order relationship | `customer_id`, `customer_unique_id` | Customer location and repeat behavior |
| `olist_products_dataset.csv` | One row per product | `product_id` | Product attributes |
| `olist_sellers_dataset.csv` | One row per seller | `seller_id` | Seller location and performance |
| `olist_geolocation_dataset.csv` | Multiple rows per postal code prefix | `geolocation_zip_code_prefix` | Geographic enrichment |
| `product_category_name_translation.csv` | One row per Portuguese category | `product_category_name` | English category labels |

Important relationship details:

1. `orders.customer_id` joins to `customers.customer_id`.
2. `customers.customer_unique_id` identifies the real customer across multiple orders.
3. `order_items.order_id` joins to `orders.order_id`.
4. `order_items.product_id` joins to `products.product_id`.
5. `order_items.seller_id` joins to `sellers.seller_id`.
6. `order_payments.order_id` and `order_reviews.order_id` join to `orders.order_id`.
7. Products join to the category translation table through `product_category_name`.
8. Geolocation is not unique at postal-code level, so aggregate or deduplicate it before joining it to customers or sellers.

## 3. Choose the Warehouse Adapter

For a local CSV project, DuckDB is a practical first choice because it can query local files and works well with dbt.

Your first setup decisions are:

1. Install Python, dbt, and the DuckDB adapter.
2. Create a local DuckDB database file such as `olist_analytics.duckdb`.
3. Decide whether CSVs will be loaded into raw tables or queried directly as external sources.
4. Prefer raw tables for repeatability once the first experiment works.
5. Keep raw tables unchanged. Apply cleaning in staging models.

Do not place business logic in the raw loading step. Raw loading should only make the CSV data available to dbt.

## 4. Phase 1: Configure dbt

### Step 1: Create the dbt project

Create the dbt project configuration and set the project name, model paths, and target database.

Use a simple project name such as `olist_dtc_analytics`.

### Step 2: Configure the connection

Configure the DuckDB profile with:

- Database file path
- Schema for development models
- Schema for production models
- Threads appropriate for your computer

Keep credentials and machine-specific settings out of version control.

### Step 3: Add basic project folders

Use the structure in Section 1. At the start, the most important folders are:

- `models/staging`
- `models/intermediate`
- `models/marts`
- `tests`
- `macros`
- `analyses`

### Step 4: Run a smoke test

Before building models, confirm that dbt can connect to the warehouse. Run a command equivalent to:

```bash
dbt debug
```

The check is successful when dbt can find the profile and connect to DuckDB.

## 5. Phase 2: Load and Declare Raw Sources

There are two reasonable approaches.

### Option A: Load CSVs into raw tables

1. Create one raw table per CSV.
2. Preserve the original column names initially.
3. Store the raw tables in a schema such as `raw`.
4. Record the load date if you plan to monitor freshness.
5. Do not remove records or rename business columns in the raw layer.

### Option B: Use external CSV sources temporarily

1. Define each CSV as a dbt source.
2. Use the warehouse's CSV reading capability.
3. Use this for exploration only if performance is acceptable.
4. Move to raw tables when you need repeatable builds and better testing.

### Source declarations

Create a source YAML file, commonly `models/staging/sources.yml`, containing one source entry for every raw table.

For each source, document:

- Source name
- Table name
- Description
- Loaded timestamp if available
- Expected primary key
- Freshness rules when a load timestamp exists

Start with source-level tests for key fields such as `order_id`, `product_id`, and `seller_id`.

## 6. Phase 3: Build Staging Models

Staging models should be one-to-one with raw tables. Their job is to make the source data consistent and usable.

Use this pattern in each staging model:

1. Select from a dbt source with `source()`.
2. Rename columns to consistent English names where needed.
3. Cast numeric columns to numeric types.
4. Cast timestamps to timestamp types.
5. Normalize text with trimming and lowercase where appropriate.
6. Convert blank strings to null when that is meaningful.
7. Add a short model description in YAML.
8. Keep joins and business metrics out of staging.

### Staging model responsibilities

#### `stg_olist__orders`

1. Keep one row per `order_id`.
2. Cast all lifecycle columns to timestamps.
3. Normalize `order_status`.
4. Preserve the original status values.
5. Add simple date fields such as purchase date only if they are broadly reusable.

#### `stg_olist__order_items`

1. Keep one row per `order_id` and `order_item_id`.
2. Cast `price` and `freight_value` to decimal or numeric types.
3. Cast `shipping_limit_date` to a timestamp.
4. Create `item_revenue` as `price`.
5. Keep freight separate from product revenue.

#### `stg_olist__order_payments`

1. Keep one row per `order_id` and `payment_sequential`.
2. Cast `payment_value` to numeric.
3. Cast `payment_installments` to integer.
4. Normalize payment type names.
5. Do not sum payments in this model because the staging grain is still one payment record.

#### `stg_olist__order_reviews`

1. Keep one row per `review_id`.
2. Cast `review_score` to integer.
3. Cast review creation and answer dates to timestamps.
4. Keep comments as nullable text.
5. Do not assume every order has exactly one review.

#### `stg_olist__customers`

1. Keep one row per `customer_id`.
2. Cast postal-code prefixes to a consistent type.
3. Normalize city and state text.
4. Preserve both `customer_id` and `customer_unique_id`.
5. Treat `customer_unique_id` as the customer-level identity for retention analysis.

#### `stg_olist__products`

1. Keep one row per `product_id`.
2. Normalize the Portuguese category name.
3. Cast dimensions and weight to numeric types.
4. Keep missing product attributes as null.
5. Preserve the source spelling of fields even if it contains a typo such as `lenght` until you rename it clearly.

#### `stg_olist__sellers`

1. Keep one row per `seller_id`.
2. Cast postal-code prefixes consistently.
3. Normalize city and state text.
4. Preserve seller location attributes.

#### `stg_olist__category_translation`

1. Keep one row per Portuguese category.
2. Normalize both category columns.
3. Use the English value when available.
4. Keep the Portuguese value as the fallback label.

#### `stg_olist__geolocation`

1. Keep the raw geolocation rows available.
2. Cast latitude and longitude to numeric.
3. Normalize city and state text.
4. Do not join this table directly to customers or sellers yet because a postal-code prefix can have multiple coordinate rows.
5. Create a later deduplicated or aggregated model for joins.

## 7. Phase 4: Add Staging Tests

Add tests before building complex joins. A failing staging test is easier to diagnose than a failing dashboard metric.

At minimum, test:

- `orders.order_id` is unique and not null.
- `customers.customer_id` is unique and not null.
- `products.product_id` is unique and not null.
- `sellers.seller_id` is unique and not null.
- `order_items.order_id` is not null.
- `order_items.product_id` is not null.
- `order_items.seller_id` is not null.
- Payment values are not negative unless you have documented a valid exception.
- Review scores are between 1 and 5 when present.
- Order status belongs to the observed status set.
- Foreign keys have accepted relationships where the source data supports them.

Run the model and test commands after staging:

```bash
dbt build --select staging
```

The exact selector syntax may depend on your folder configuration. The important rule is to validate staging before moving forward.

## 8. Phase 5: Build Intermediate Models

Intermediate models solve repeated joins and aggregation problems. They are not the final analytics tables.

### `int_olist__order_payments`

Purpose: produce one row per order for payment analysis.

Steps:

1. Start from staged payment records.
2. Group by `order_id`.
3. Sum `payment_value` into `total_payment_value`.
4. Count payment records.
5. Count distinct payment types.
6. Calculate the maximum number of installments.
7. Keep the payment-level staging model for detailed analysis.

### `int_olist__order_reviews`

Purpose: produce order-level review metrics without multiplying orders.

Steps:

1. Start from staged review records.
2. Group by `order_id`.
3. Calculate average review score.
4. Count review records.
5. Calculate the earliest review creation timestamp.
6. Calculate the latest answer timestamp.
7. Keep the review-level staging model for comment analysis.

### `int_olist__order_items_enriched`

Purpose: enrich each order item with product, category, seller, and order context.

Steps:

1. Start from staged order items.
2. Join products on `product_id`.
3. Join category translation on the normalized Portuguese category.
4. Join sellers on `seller_id`.
5. Join orders on `order_id`.
6. Calculate item-level revenue and item-level freight.
7. Add delivery and customer identifiers needed by downstream models.
8. Confirm the row count has not unexpectedly increased after every join.

The grain must remain one row per `order_id` and `order_item_id`.

### `int_olist__orders_enriched`

Purpose: create one order-level table with reusable order metrics.

Steps:

1. Start from staged orders.
2. Join customers on `customer_id`.
3. Join aggregated payments on `order_id`.
4. Join aggregated reviews on `order_id`.
5. Aggregate order items by `order_id` before joining them.
6. Calculate item count, product revenue, and freight value.
7. Calculate delivery days when both purchase and delivery timestamps exist.
8. Calculate delivery delay days by comparing actual delivery to estimated delivery.
9. Preserve nulls when an order has not been delivered.

The grain must remain one row per `order_id`.

## 9. Phase 6: Build Core Marts

Marts are the tables that analysts and dashboards should use. Each mart should have a clear grain and a business-friendly name.

### `fct_orders`

Grain: one row per order.

Include:

- Order and customer identifiers
- Order status
- Purchase, approval, delivery, and estimated delivery timestamps
- Product revenue
- Freight value
- Total payment value
- Item count
- Review score summary
- Delivery duration
- Delivery delay
- Customer location

Use this as the primary order performance fact table.

### `fct_order_items`

Grain: one row per order item.

Include:

- Order item identifiers
- Order date
- Product and category identifiers
- Seller identifier
- Product price
- Freight value
- Item revenue
- Customer state
- Seller state

Use this for product, category, and seller analysis.

### `dim_customers`

Grain: one row per `customer_unique_id`.

Steps:

1. Group customer-order records by `customer_unique_id`.
2. Count distinct orders.
3. Find first and last order dates.
4. Add customer state and city using a documented rule.
5. Add lifetime product revenue from the order or item fact table.
6. Add a repeat-customer flag.

Do not use `customer_id` as the repeat-customer identity because the source can assign different order-level customer IDs to the same real customer.

### `dim_products`

Grain: one row per `product_id`.

Include:

- Product attributes
- Portuguese category
- English category
- Product dimensions
- Product weight
- Product photo count

Add sales metrics only if you clearly label this as a product performance dimension or create a separate aggregate table. Avoid mixing descriptive attributes and changing metrics without a reason.

### `dim_sellers`

Grain: one row per `seller_id`.

Include:

- Seller location
- State and city
- Order count
- Item count
- Revenue
- Average review score where the relationship is meaningful
- Average delivery or shipping performance where measurable

## 10. Phase 7: Build Business Marts

### Finance mart

`finance_daily_metrics` grain: one row per calendar day.

Steps:

1. Choose the purchase date as the default business date.
2. Count distinct orders.
3. Count sold items.
4. Sum product revenue.
5. Sum freight value.
6. Sum total payment value carefully.
7. Calculate average order value.
8. Separate delivered, canceled, and unavailable orders.
9. Document whether canceled orders are included in revenue.

Avoid summing payment totals after joining to item-level rows. That would duplicate payment values.

### Customer mart

`customer_order_summary` grain: one row per customer.

Include:

- Total orders
- First order date
- Last order date
- Total product revenue
- Average order value
- Average review score
- Repeat customer flag
- Customer state

`customer_retention` grain: one row per cohort month and activity month, or one row per customer-month depending on the design.

Steps:

1. Find each customer's first purchase month.
2. Find each subsequent purchase month.
3. Calculate months since first purchase.
4. Count active customers by cohort and month number.
5. Divide active customers by the original cohort size.
6. Exclude or separately label incomplete recent cohorts.

### Product mart

`product_performance` grain: one row per product.

Include:

- Units sold
- Order count
- Product revenue
- Freight revenue or cost
- Average item price
- Average review score
- Cancellation or unavailable-order exposure

`category_performance` grain: one row per translated category.

Include:

- Units sold
- Orders containing the category
- Revenue
- Average price
- Average review score
- Share of total revenue

### Operations mart

`delivery_performance` grain: one row per order or one row per reporting period, depending on the purpose.

Calculate:

- Purchase-to-delivery days
- Purchase-to-carrier days
- Carrier-to-customer days
- Estimated delivery delay days
- On-time delivery flag
- Delivery metrics by state, seller, and category

`review_performance` grain: one row per order review or one row per reporting period.

Calculate:

- Average review score
- Review count
- Low-score rate
- Review response time
- Review score by category, state, and delivery-delay bucket

`seller_performance` grain: one row per seller.

Calculate:

- Orders handled
- Items sold
- Revenue
- Freight value
- Average review score
- On-time delivery rate
- Average delivery delay

## 11. Phase 8: Use SQL Safely with Multiple Grains

Most errors in this project will come from joining tables with different grains.

Before every join, write down:

```text
Left model grain: one row per ______
Right model grain: one row per ______
Expected output grain: one row per ______
Join key: ______
Can the right side have multiple rows per key? yes/no
```

Rules to follow:

1. Aggregate payments to order grain before joining payments to orders.
2. Aggregate reviews to order grain before joining reviews to orders.
3. Aggregate order items to order grain before joining items to orders.
4. Join product and seller attributes at item grain.
5. Never use `SELECT *` in final marts.
6. Use explicit column lists and meaningful aliases.
7. Check row counts before and after joins.
8. Check totals before and after joins.

## 12. Phase 9: Add Data Quality Tests

Add generic dbt tests in YAML for:

- `unique`
- `not_null`
- `accepted_values`
- `relationships`

Add custom SQL tests in `tests/` for business rules such as:

1. No order has a delivery timestamp earlier than its purchase timestamp.
2. No delivered order has a missing delivery timestamp.
3. No negative product price exists.
4. No review score is outside 1 to 5.
5. The order-level fact has exactly one row per `order_id`.
6. The item-level fact has exactly one row per `order_id` and `order_item_id`.
7. Order revenue is not duplicated by payment joins.
8. Product revenue in a daily aggregate reconciles to the item fact table.
9. A customer's last order date is not earlier than the first order date.
10. A seller or product dimension does not have duplicate keys.

Run tests after each model layer instead of waiting until the entire warehouse is complete.

## 13. Phase 10: Add Documentation

For every model, document:

- What the model represents
- Its grain
- Its owner or intended user
- Its important columns
- Its upstream dependencies
- Any assumptions
- Any exclusions

For important columns, document:

- Definition
- Data type
- Calculation
- Null behavior
- Whether it can be safely summed

Examples of assumptions to document:

- Product revenue is `price`, while freight is kept separate.
- Payment total is the sum of payment records by order.
- Repeat customers are identified by `customer_unique_id`.
- Revenue date is the order purchase date.
- Undelivered orders do not receive a delivery-duration value.
- Geolocation is optional enrichment because postal prefixes can map to multiple coordinates.

## 14. Phase 11: Use Analyses for Exploration

Put exploratory SQL in `analyses/` rather than mixing it into production models.

Good first analyses:

1. Monthly orders and revenue.
2. Top product categories by revenue.
3. Revenue by customer state.
4. Average review score by delivery-delay bucket.
5. Repeat-customer rate by first-purchase month.
6. Sellers with high revenue and poor delivery performance.
7. Products with many orders but low review scores.
8. Payment method and installment patterns.

Once an analysis becomes a stable business requirement, convert it into a documented mart model.

## 15. Phase 12: Add Macros Only When Repetition Appears

Start with normal SQL. Add a macro only when the same logic appears in multiple models.

Potential macros later:

- Standard date-spine generation
- Safe division that returns null or zero by policy
- Consistent surrogate key creation
- Reusable customer retention calculations
- Reusable delivery bucket logic

Keep macros small and test them with representative inputs.

## 16. Phase 13: Optional Snapshots

Snapshots are optional for this dataset because the CSV files are historical extracts rather than a continuously changing operational source.

Use snapshots only if you later receive repeated extracts and need to track changes in:

- Order status
- Delivery milestones
- Product attributes
- Seller attributes

Before adding a snapshot, decide:

1. What column identifies a record.
2. What column or columns indicate a change.
3. How often the source is loaded.
4. Whether historical versions are analytically meaningful.

## 17. Recommended Build Order

Complete the project in this order:

1. Confirm the warehouse adapter and connection.
2. Load or expose the nine raw CSV sources.
3. Declare sources in dbt.
4. Build and test all staging models.
5. Build and test order-level payment and review aggregations.
6. Build and test enriched order-item and order models.
7. Build the core facts and dimensions.
8. Build finance and product marts.
9. Build customer retention and operations marts.
10. Add custom data tests.
11. Add documentation and column descriptions.
12. Add analyses for business questions.
13. Optimize only after correctness is proven.

## 18. Milestones and Completion Checks

### Milestone 1: Sources work

- dbt connection succeeds.
- Every CSV is available as a source.
- Raw row counts are recorded.

### Milestone 2: Staging works

- All columns have sensible data types.
- Keys and null behavior are understood.
- Staging tests pass.

### Milestone 3: Grain is controlled

- Payment and review records are aggregated before order joins.
- Item joins do not unexpectedly multiply rows.
- Order and item grains are documented.

### Milestone 4: Core marts work

- `fct_orders` has one row per order.
- `fct_order_items` has one row per order item.
- Customer, product, and seller dimensions have stable keys.

### Milestone 5: Business metrics reconcile

- Daily revenue reconciles to the item fact.
- Order counts reconcile to the order fact.
- Payment totals are not duplicated.
- Retention counts use unique customers.

### Milestone 6: The warehouse is usable

- Models are documented.
- Tests run with the normal build command.
- Analysts can answer the core business questions using marts rather than raw tables.

## 19. First Practical Task List

Use this as the first implementation checklist:

- [ ] Choose DuckDB and configure dbt.
- [ ] Decide whether to load CSVs into raw tables or query them as external sources.
- [ ] Define all nine sources.
- [ ] Create the nine staging model files.
- [ ] Add source and staging tests.
- [ ] Run staging and inspect row counts.
- [ ] Build payment and review order-level aggregations.
- [ ] Build the enriched order-item model.
- [ ] Build the enriched order model.
- [ ] Create `fct_orders` and `fct_order_items`.
- [ ] Create customer, product, and seller dimensions.
- [ ] Add finance, customer, product, and operations marts.
- [ ] Add custom SQL tests for grain and reconciliation.
- [ ] Document every final model and metric.
- [ ] Move exploratory queries into `analyses/`.

The most important principle is to make every model's grain explicit before writing its joins. If the grain is correct, the rest of the warehouse becomes much easier to reason about and test.
