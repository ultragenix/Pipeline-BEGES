{{ config(materialized='table') }}

with ranked as (
    select
        *,
        row_number() over (
            partition by company_code, coalesce(impact_group, constat_id)
            order by impact_tco2e desc nulls last, impact_eur desc nulls last
        ) as impact_rank
    from {{ ref('quality_constats') }}
),

summarized as (
    select
        company_code,
        company_name,
        count(*) as nb_constats,
        count(*) filter (where severity = 'bloquant') as nb_bloquants,
        count(*) filter (where severity = 'alerte') as nb_alertes,
        count(*) filter (where severity = 'info') as nb_infos,
        count(*) filter (where certitude = 'certain') as nb_certains,
        count(*) filter (where statut = 'a_confirmer') as nb_a_confirmer,
        count(*) filter (where statut = 'ouvert') as nb_ouverts,
        coalesce(
            sum(case when impact_rank = 1 then impact_tco2e end),
            0
        ) as impact_tco2e,
        coalesce(
            sum(case when impact_rank = 1 then impact_eur end),
            0
        ) as impact_eur
    from ranked
    group by 1, 2
)

select * from summarized
