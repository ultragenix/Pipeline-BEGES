with fec as (
    select *
    from {{ ref('stg_fec') }}
    where account_class = '6' or account like '21%'
),

mapped as (
    select
        f.*,
        m.prefix as mapping_prefix,
        m.libelle as mapping_label,
        m.poste as mapping_poste,
        m.scope as mapping_scope,
        m.ratio_kgco2e_par_keur,
        m.replaced_by,
        m.mapping_type,
        row_number() over (
            partition by f.company_code, f.source_id, f.source_row
            order by length(m.prefix) desc nulls last
        ) as mapping_rank
    from fec f
    left join {{ ref('ref_account_mapping') }} m
        on starts_with(f.account, m.prefix)
),

classified as (
    select
        *,
        case
            when mapping_prefix is null then 'compte_non_mappe'
            when replaced_by = 'hors_perimetre' then 'hors_perimetre'
            when replaced_by is not null then 'couvert_par_physique'
            when ratio_kgco2e_par_keur is null then 'ratio_absent'
            else null
        end as exclusion_reason
    from mapped
    where mapping_rank = 1
)

select
    company_code || ':fec:' || source_id || ':' || source_row as emission_id,
    company_code,
    'fec' as source_type,
    source_id,
    source_file,
    source_sheet,
    source_row,
    ingestion_id,
    ingested_at,
    mapping_scope as scope,
    coalesce(mapping_poste, 'Non mappé') as poste,
    coalesce(mapping_label, account_label) as activity,
    case
        when exclusion_reason is null then 'monetaire'
        else 'non_calcule'
    end as method,
    amount_ht_eur as activity_value,
    'EUR' as activity_unit,
    ratio_kgco2e_par_keur as emission_factor,
    'kgCO2e/k€' as emission_factor_unit,
    case
        when exclusion_reason is null
        then amount_ht_eur * ratio_kgco2e_par_keur / 1000000
    end as tco2e,
    amount_ht_eur as amount_source_eur,
    'HT' as amount_source_basis,
    amount_ht_eur,
    exclusion_reason is null as is_included,
    exclusion_reason,
    case when amount_ht_eur < 0 then 'montant_negatif' end as quality_flag,
    account as source_reference
from classified
