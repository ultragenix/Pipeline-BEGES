with source as (
    select * from {{ source('raw', 'electricity') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by
                company_code,
                source_id,
                site_code,
                month,
                pdl,
                consumption_kwh,
                amount_ht_eur,
                reading_type
            order by source_row
        ) as duplicate_rank
    from source
)

select
    *,
    duplicate_rank > 1 as is_exact_duplicate
from ranked
