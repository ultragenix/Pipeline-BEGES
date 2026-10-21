-- Chaque entrée du registre doit avoir un constat calculé.
select r.constat_id
from {{ ref('ref_quality_register') }} r
left join {{ ref('quality_constats') }} q on r.constat_id = q.constat_id
where q.constat_id is null
