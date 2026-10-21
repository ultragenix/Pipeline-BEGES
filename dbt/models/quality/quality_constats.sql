{{ config(materialized='table') }}

with register as (
    select * from {{ ref('ref_quality_register') }}
),

findings as (
    select * from {{ ref('int_quality_findings') }}
),

joined as (
    select
        r.constat_id,
        r.registry_id,
        r.company_code,
        coalesce(c.company_name, 'Toutes les entreprises') as company_name,
        r.source_type,
        r.family,
        r.severity,
        r.certitude,
        r.statut,
        r.traitement,
        r.title,
        trim(
            r.proof_detail
            || case
                when f.evidence_lines is null
                 and f.evidence_quantity is null
                 and f.evidence_amount_eur is null
                then ''
                else ' ' || concat_ws(
                    ', ',
                    case
                        when f.evidence_lines is not null
                        then printf('%d ligne(s)', f.evidence_lines)
                    end,
                    case
                        when f.evidence_quantity is not null
                            and f.evidence_quantity = round(f.evidence_quantity)
                        then printf(
                            '%.0f %s',
                            f.evidence_quantity,
                            f.evidence_quantity_unit
                        )
                        when f.evidence_quantity is not null
                        then printf(
                            '%.2f %s',
                            f.evidence_quantity,
                            f.evidence_quantity_unit
                        )
                    end,
                    case
                        when f.evidence_amount_eur is not null
                        then printf(
                            '%.2f € %s',
                            f.evidence_amount_eur,
                            f.evidence_amount_basis
                        )
                    end
                ) || '.'
            end
        ) as proof,
        r.business_question,
        f.evidence_lines,
        f.evidence_quantity,
        f.evidence_quantity_unit,
        f.evidence_amount_eur,
        f.evidence_amount_basis,
        f.impact_tco2e,
        f.impact_eur,
        r.impact_type,
        r.impact_group,
        r.impact_basis,
        f.source_file,
        f.source_row,
        r.check_key,
        case r.severity
            when 'bloquant' then 1
            when 'alerte' then 2
            else 3
        end as severity_rank,
        case r.statut
            when 'ouvert' then 1
            when 'a_confirmer' then 2
            when 'repondu' then 3
            when 'integre' then 4
            else 5
        end as statut_rank
    from register r
    join findings f
      on r.check_key = f.check_key
     and r.company_code = f.company_code
     and coalesce(r.match_key, '') = coalesce(f.match_key, '')
    left join {{ ref('ref_companies') }} c on r.company_code = c.company_code
)

select * from joined
