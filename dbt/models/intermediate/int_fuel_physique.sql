with source as (
    select * from {{ ref('stg_fuel') }}
),

params as (
    select
        vat_rate,
        gazole_price_ttc_eur_per_l,
        sp95_price_ttc_eur_per_l
    from {{ ref('ref_parameters') }}
),

factors as (
    select code, value
    from {{ ref('ref_emission_factors') }}
    where category = 'fuel'
),

priced as (
    select
        s.*,
        case s.product_code
            when 'GAZOLE' then p.gazole_price_ttc_eur_per_l
            when 'SP95' then p.sp95_price_ttc_eur_per_l
        end as price_ttc_eur_per_l,
        p.vat_rate
    from source s
    cross join params p
),

enriched as (
    select
        pr.*,
        f.value as emission_factor,
        case
            when pr.quantity_l is not null then pr.quantity_l
            when pr.price_ttc_eur_per_l is not null
                then pr.amount_ttc_eur / pr.price_ttc_eur_per_l
        end as quantity_l_final
    from priced pr
    left join factors f on pr.product_code = f.code
),

flagged as (
    select
        *,
        (
            product_code in ('GAZOLE', 'SP95')
            and emission_factor is not null
            and quantity_l_final is not null
        ) as is_included,
        case
            when product_code = 'NON_CARBURANT' then 'non_combustible'
            when product_code = 'INCONNU' then 'produit_inconnu'
            when emission_factor is null then 'facteur_absent'
            when quantity_l_final is null then 'quantite_absente'
            else null
        end as exclusion_reason
    from enriched
)

select
    company_code || ':fuel:' || source_id || ':' || source_row as emission_id,
    company_code,
    'fuel' as source_type,
    source_id,
    source_file,
    source_sheet,
    source_row,
    ingestion_id,
    ingested_at,
    1 as scope,
    'Combustion mobile' as poste,
    'Carburants' as activity,
    case
        when product_code in ('NON_CARBURANT', 'INCONNU') then 'non_calcule'
        when quantity_l is not null then 'physique'
        when quantity_l_final is not null then 'physique_estimee'
        else 'non_calcule'
    end as method,
    quantity_l_final as activity_value,
    'L' as activity_unit,
    emission_factor,
    'kgCO2e/L' as emission_factor_unit,
    case
        when is_included
        then quantity_l_final * emission_factor / 1000
    end as tco2e,
    amount_ttc_eur as amount_source_eur,
    'TTC' as amount_source_basis,
    amount_ttc_eur / (1 + vat_rate) as amount_ht_eur,
    is_included,
    exclusion_reason,
    case
        when quantity_l is null and quantity_l_final is not null
            then 'litres_estimes'
        when product_confidence = 'a_confirmer'
            then 'produit_a_confirmer'
    end as quality_flag,
    card_id as source_reference
from flagged
