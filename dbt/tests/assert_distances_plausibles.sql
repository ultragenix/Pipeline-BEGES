select *
from {{ ref('int_flights_physique') }}
where activity_value is not null
    and (activity_value < 95 or activity_value > 40000)

union all

select f.*
from {{ ref('int_flights_physique') }} f
inner join {{ ref('stg_flights') }} s
    on f.company_code = s.company_code
    and f.source_id = s.source_id
    and f.source_row = s.source_row
where s.origin_iata = 'RUN'
    and s.destination_iata = 'CDG'
    and (f.activity_value < 8000 or f.activity_value > 22000)
