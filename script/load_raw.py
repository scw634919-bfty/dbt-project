import duckdb

con = duckdb.connect("olist_analytics.duckdb")

# Create raw schema
con.execute("CREATE SCHEMA IF NOT EXISTS raw")

# Load orders CSV
con.execute("""
    CREATE OR REPLACE TABLE raw.orders AS
    SELECT *
    FROM read_csv_auto('dataset/olist_orders_dataset.csv')
""")

# Load customers CSV
con.execute("""
    CREATE OR REPLACE TABLE raw.customers AS
    SELECT *
    FROM read_csv_auto('dataset/olist_customers_dataset.csv')
""")

# Load products CSV
con.execute("""
    CREATE OR REPLACE TABLE raw.products AS
    SELECT *
    FROM read_csv_auto('dataset/olist_products_dataset.csv')
""")

# Load geolocation CSV
con.execute("""
    CREATE OR REPLACE TABLE raw.geolocation AS
    SELECT *
    FROM read_csv_auto('dataset/olist_geolocation_dataset.csv')
""")

# Load order items CSV
con.execute("""
    CREATE OR REPLACE TABLE raw.order_items AS
    SELECT *
    FROM read_csv_auto('dataset/olist_order_items_dataset.csv')
""")

# Load order payments CSV
con.execute("""
    CREATE OR REPLACE TABLE raw.order_payments AS
    SELECT *
    FROM read_csv_auto('dataset/olist_order_payments_dataset.csv')
""")

# Load order reviews CSV
con.execute("""
    CREATE OR REPLACE TABLE raw.order_reviews AS
    SELECT *
    FROM read_csv_auto('dataset/olist_order_reviews_dataset.csv')
""")

# Load sellers CSV
con.execute("""
    CREATE OR REPLACE TABLE raw.sellers AS
    SELECT *
    FROM read_csv_auto('dataset/olist_sellers_dataset.csv')
""")

# Load category name translation CSV
con.execute("""
    CREATE OR REPLACE TABLE raw.category_name_translation AS
    SELECT *
    FROM read_csv_auto('dataset/product_category_name_translation.csv')
""")

con.close()

print("Raw tables created successfully!")