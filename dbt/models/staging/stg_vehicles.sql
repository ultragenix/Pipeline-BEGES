select
    *,
    company_code || ':' || vehicle_id as vehicle_key
from {{ source('raw', 'vehicles') }}
