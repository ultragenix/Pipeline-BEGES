with facts as (
    select * from {{ ref('fct_emissions') }}
),

companies as (
    select * from {{ ref('ref_companies') }}
)

select
    f.company_code,
    c.company_name,
    f.scope,
    f.poste,
    f.activity,
    f.method,
    count(*) as lignes,
    sum(f.tco2e) as tco2e,
    sum(
        case
            when f.method in ('physique', 'physique_estimee') then f.tco2e
            else 0
        end
    ) as tco2e_physique,
    sum(
        case when f.method = 'monetaire' then f.tco2e else 0 end
    ) as tco2e_monetaire,
    sum(
        case
            when f.method in ('physique', 'physique_estimee') then f.tco2e
            else 0
        end
    ) / nullif(sum(f.tco2e), 0) as part_physique,
    sum(f.amount_ht_eur) as amount_ht_eur,
    f.company_code || ':' || cast(f.scope as varchar) || ':' || f.poste
        || ':' || f.activity || ':' || f.method as beges_key
from facts f
left join companies c on f.company_code = c.company_code
group by 1, 2, 3, 4, 5, 6
