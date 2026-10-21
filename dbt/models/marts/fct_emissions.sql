select
    *,
    case
        when method = 'monetaire' then 'monetaire'
        when method = 'non_calcule' then 'non_calcule'
        else 'physique'
    end as method_family
from {{ ref('int_emissions_candidates') }}
where is_included
