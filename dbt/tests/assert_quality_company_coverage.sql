-- Chaque entreprise doit conserver la couverture de son registre d'origine.
select company_code, count(*) as nb_constats
from {{ ref('quality_constats') }}
where registry_id is not null
group by 1
having (company_code = 'KAY' and count(*) < 14)
    or (company_code = 'FAN' and count(*) < 13)
    or (company_code = 'VAC' and count(*) < 11)
