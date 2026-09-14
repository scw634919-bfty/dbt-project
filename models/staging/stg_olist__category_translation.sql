select
    lower(trim(product_category_name)) as product_category_name,

    nullif(
        lower(trim(product_category_name_english)),
        ''
    ) as product_category_name_english,

    coalesce(
        nullif(lower(trim(product_category_name_english)), ''),
        lower(trim(product_category_name))
    ) as category_name

from {{ source('raw', 'category_translation') }}