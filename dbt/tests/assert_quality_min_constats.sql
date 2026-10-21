-- Le registre doit contenir au moins 15 constats.
select count(*) as nb_constats
from {{ ref('quality_constats') }}
having count(*) < 15
