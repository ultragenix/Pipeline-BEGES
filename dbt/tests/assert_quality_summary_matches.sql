-- La synthèse par entreprise doit réconcilier le nombre de constats.
with summary as (
    select sum(nb_constats) as nb
    from {{ ref('quality_summary') }}
),

details as (
    select count(*) as nb
    from {{ ref('quality_constats') }}
)

select s.nb as nb_synthese, d.nb as nb_detail
from summary s
cross join details d
where s.nb <> d.nb
