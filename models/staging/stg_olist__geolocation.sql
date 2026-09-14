select
    cast(geolocation_zip_code_prefix as varchar) as geolocation_zip_code_prefix,

    cast(geolocation_lat as double) as geolocation_lat,
    cast(geolocation_lng as double) as geolocation_lng,

    lower(trim(geolocation_city)) as geolocation_city,
    upper(trim(geolocation_state)) as geolocation_state

from {{ source('raw', 'geolocation') }}