with source as (
    select * from {{ source('raw', 'flights') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by
                company_code,
                source_id,
                ticket_id,
                emission_date,
                departure_date,
                traveler_id,
                origin_iata,
                destination_iata,
                trip_type,
                cabin_class,
                status,
                amount_ttc_eur
            order by source_row
        ) as duplicate_rank
    from source
)

select
    *,
    duplicate_rank > 1 as is_exact_duplicate,
    status = 'Annulé' as is_cancelled,
    trip_type = 'AR' as is_round_trip
from ranked
