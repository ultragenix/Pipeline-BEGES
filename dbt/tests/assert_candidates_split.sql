with counts as (
    select
        (select count(*) from {{ ref('int_emissions_candidates') }})
            as candidates,
        (select count(*) from {{ ref('fct_emissions') }}) as included,
        (select count(*) from {{ ref('fct_exclusions') }}) as excluded
)

select *
from counts
where candidates <> included + excluded
