-- Chaque constat calculé doit être décrit dans le registre.
select
    f.check_key,
    f.company_code,
    f.match_key
from {{ ref('int_quality_findings') }} f
left join {{ ref('ref_quality_register') }} r
  on f.check_key = r.check_key
 and f.company_code = r.company_code
 and coalesce(f.match_key, '') = coalesce(r.match_key, '')
where r.constat_id is null
