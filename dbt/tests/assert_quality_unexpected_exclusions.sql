-- Toute exclusion inattendue doit être couverte par un constat.
-- Les remplacements physiques et le hors-périmètre sont des choix méthodologiques documentés.
with unexpected as (
    select distinct company_code, exclusion_reason
    from {{ ref('fct_exclusions') }}
    where exclusion_reason not in ('couvert_par_physique', 'hors_perimetre')
),

covered as (
    select distinct company_code, check_key
    from {{ ref('quality_constats') }}
    where check_key like 'exclusion.%'
)

select u.company_code, u.exclusion_reason
from unexpected u
where not exists (
    select 1
    from covered c
    where c.company_code = u.company_code
      and c.check_key = 'exclusion.' || u.exclusion_reason
)
