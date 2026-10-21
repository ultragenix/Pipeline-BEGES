with source as (
    select * from {{ ref('stg_refrigerants') }}
),

factors as (
    select
        upper(code) as code,
        value
    from {{ ref('ref_emission_factors') }}
    where category = 'refrigerant'
),

enriched as (
    select
        s.*,
        f.value as gwp
    from source s
    left join factors f on s.fluid_code_norm = f.code
)

select
    company_code || ':refrigerants:' || source_id || ':' || source_row
        as emission_id,
    company_code,
    'refrigerants' as source_type,
    source_id,
    source_file,
    source_sheet,
    source_row,
    ingestion_id,
    ingested_at,
    1 as scope,
    'Fuites frigorigènes' as poste,
    'Fluides frigorigènes' as activity,
    case when gwp is null then 'non_calcule' else 'physique' end as method,
    recharge_kg as activity_value,
    'kg' as activity_unit,
    gwp as emission_factor,
    'kgCO2e/kg' as emission_factor_unit,
    case when gwp is not null then recharge_kg * gwp / 1000 end as tco2e,
    cast(null as double) as amount_source_eur,
    cast(null as varchar) as amount_source_basis,
    cast(null as double) as amount_ht_eur,
    gwp is not null as is_included,
    case when gwp is null then 'gwp_inconnu' end as exclusion_reason,
    case
        when recharge_kg > nominal_charge_kg then 'recharge_superieure_charge'
        when gwp is null then 'gwp_inconnu'
    end as quality_flag,
    equipment as source_reference
from enriched
