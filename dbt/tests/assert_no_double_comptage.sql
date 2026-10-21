with method_families as (
    select
        company_code,
        activity,
        count(
            distinct case
                when method = 'monetaire' then 'monetaire'
                else 'physique'
            end
        ) as families
    from {{ ref('fct_emissions') }}
    group by 1, 2
)

select *
from method_families
where families > 1
