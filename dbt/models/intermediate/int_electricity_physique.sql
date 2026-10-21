with source as (
    select * from {{ ref('stg_electricity') }}
),

params as (
    select electricity_factor_kg_per_kwh as factor
    from {{ ref('ref_parameters') }}
)

select
    company_code || ':electricity:' || source_id || ':'
        || coalesce(source_sheet, '') || ':' || source_row as emission_id,
    company_code,
    'electricity' as source_type,
    source_id,
    source_file,
    source_sheet,
    source_row,
    ingestion_id,
    ingested_at,
    2 as scope,
    'Électricité' as poste,
    'Électricité' as activity,
    'physique' as method,
    consumption_kwh as activity_value,
    'kWh' as activity_unit,
    p.factor as emission_factor,
    'kgCO2e/kWh' as emission_factor_unit,
    consumption_kwh * p.factor / 1000 as tco2e,
    amount_ht_eur as amount_source_eur,
    'HT' as amount_source_basis,
    amount_ht_eur,
    not is_exact_duplicate as is_included,
    case when is_exact_duplicate then 'doublon_exact' end as exclusion_reason,
    case
        when reading_type = 'Estimé' then 'releve_estime'
        when reading_type = 'Régularisation' then 'regularisation'
    end as quality_flag,
    coalesce(pdl, site_code) as source_reference
from source
cross join params p
