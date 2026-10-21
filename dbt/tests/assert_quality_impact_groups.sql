-- Un impact partagé doit concerner au moins deux constats et être chiffré.
select impact_group
from {{ ref('quality_constats') }}
where impact_group is not null
group by 1
having count(*) < 2
    or count(*) filter (where impact_tco2e is null) > 0
