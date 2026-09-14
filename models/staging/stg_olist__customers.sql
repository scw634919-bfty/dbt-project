select
    customer_id,
    customer_unique_id,

    cast(customer_zip_code_prefix as varchar) as customer_zip_code_prefix,

    lower(trim(customer_city)) as customer_city,
    upper(trim(customer_state)) as customer_state

from {{ source('raw', 'customers') }}