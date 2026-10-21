select
    * exclude (tco2e),
    tco2e as tco2e_non_compte,
    case
        when method = 'monetaire' then 'monetaire'
        when method = 'non_calcule' then 'non_calcule'
        else 'physique'
    end as method_family
from {{ ref('int_emissions_candidates') }}
where not is_included
