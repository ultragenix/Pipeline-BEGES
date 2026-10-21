with fct as (
    select
        company_code,
        sum(tco2e) as tco2e
    from {{ ref('fct_emissions') }}
    group by 1
),

mart as (
    select
        company_code,
        sum(tco2e) as tco2e
    from {{ ref('mart_beges') }}
    group by 1
)

select coalesce(f.company_code, m.company_code) as company_code
from fct f
full outer join mart m on f.company_code = m.company_code
where abs(coalesce(f.tco2e, 0) - coalesce(m.tco2e, 0)) > 0.000001
