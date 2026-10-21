{{ config(materialized='view') }}

with

params as (
    select
        p.electricity_factor_kg_per_kwh,
        p.gazole_factor_kg_per_l,
        p.gazole_price_ttc_eur_per_l,
        p.vat_rate,
        (
            select value
            from {{ ref('ref_emission_factors') }}
            where factor_key = 'price:electricity_ht_eur_per_kwh'
        ) as electricity_price_ht_eur_per_kwh
    from {{ ref('ref_parameters') }} p
),

electricity_totals as (
    select
        company_code,
        sum(amount_ht_eur) as electricity_eur,
        sum(consumption_kwh) as electricity_kwh
    from {{ ref('stg_electricity') }}
    group by 1
),

fec_electricity_totals as (
    select
        company_code,
        sum(debit - credit) as fec_eur
    from {{ ref('stg_fec') }}
    where starts_with(account, '60611')
    group by 1
),

electricity_gaps as (
    select
        coalesce(e.company_code, f.company_code) as company_code,
        coalesce(e.electricity_eur, 0) as electricity_eur,
        coalesce(f.fec_eur, 0) as fec_eur,
        coalesce(f.fec_eur, 0) - coalesce(e.electricity_eur, 0) as gap_eur
    from electricity_totals e
    full outer join fec_electricity_totals f on e.company_code = f.company_code
),

fuel_totals as (
    select
        f.company_code,
        sum(f.amount_ttc_eur) / (1 + p.vat_rate) as fuel_ht_eur
    from {{ ref('stg_fuel') }} f
    cross join params p
    where f.product_code in ('GAZOLE', 'SP95')
    group by f.company_code, p.vat_rate
),

fec_fuel_totals as (
    select
        company_code,
        sum(debit - credit) as fec_eur
    from {{ ref('stg_fec') }}
    where starts_with(account, '60622')
    group by 1
),

fuel_gaps as (
    select
        coalesce(f.company_code, x.company_code) as company_code,
        coalesce(f.fuel_ht_eur, 0) as fuel_ht_eur,
        coalesce(x.fec_eur, 0) as fec_eur,
        coalesce(x.fec_eur, 0) - coalesce(f.fuel_ht_eur, 0) as gap_eur
    from fuel_totals f
    full outer join fec_fuel_totals x on f.company_code = x.company_code
),

missing_electricity_sites as (
    select
        s.company_code,
        string_agg(s.site_code, ', ' order by s.site_code) as sites,
        count(*) as nb_sites
    from {{ ref('ref_sites') }} s
    where not exists (
        select 1
        from {{ ref('stg_electricity') }} e
        where e.company_code = s.company_code
          and e.site_code = s.site_code
    )
    group by s.company_code
),

electricity_site_findings as (
    select
        'electricity.site_missing' as check_key,
        m.company_code,
        cast(null as varchar) as match_key,
        cast(null as integer) as evidence_lines,
        cast(m.nb_sites as double) as evidence_quantity,
        'site(s)' as evidence_quantity_unit,
        cast(null as double) as evidence_amount_eur,
        cast(null as varchar) as evidence_amount_basis,
        cast(
            abs(g.gap_eur)
            / p.electricity_price_ht_eur_per_kwh
            * p.electricity_factor_kg_per_kwh
            / 1000
            as double
        ) as impact_tco2e,
        cast(abs(g.gap_eur) as double) as impact_eur,
        'Sites sans relevé : ' || m.sites || '.' as proof_extra,
        cast(null as varchar) as source_file,
        cast(null as integer) as source_row
    from missing_electricity_sites m
    join electricity_gaps g on m.company_code = g.company_code
    cross join params p
),

missing_refrigerant_sites as (
    select
        s.company_code,
        string_agg(s.site_code, ', ' order by s.site_code) as sites,
        count(*) as nb_sites
    from {{ ref('ref_sites') }} s
    where not exists (
        select 1
        from {{ ref('stg_refrigerants') }} r
        where r.company_code = s.company_code
          and r.site_code = s.site_code
    )
    group by s.company_code
),

refrigerant_site_findings as (
    select
        'refrigerant.site_missing' as check_key,
        company_code,
        cast(null as varchar) as match_key,
        cast(null as integer) as evidence_lines,
        cast(nb_sites as double) as evidence_quantity,
        'site(s)' as evidence_quantity_unit,
        cast(null as double) as evidence_amount_eur,
        cast(null as varchar) as evidence_amount_basis,
        cast(null as double) as impact_tco2e,
        cast(null as double) as impact_eur,
        'Sites sans intervention : ' || sites || '.' as proof_extra,
        cast(null as varchar) as source_file,
        cast(null as integer) as source_row
    from missing_refrigerant_sites
),

months as (
    select
        cast(unnest(generate_series(
            date '2025-01-01',
            date '2025-12-01',
            interval 1 month
        )) as date) as month
),

electricity_site_months as (
    select distinct company_code, site_code
    from {{ ref('stg_electricity') }}
),

missing_months as (
    select
        sm.company_code,
        count(*) as missing_site_months
    from electricity_site_months sm
    cross join months m
    where not exists (
        select 1
        from {{ ref('stg_electricity') }} e
        where e.company_code = sm.company_code
          and e.site_code = sm.site_code
          and e.month = m.month
    )
    group by sm.company_code
),

electricity_coverage as (
    select
        company_code,
        count(distinct site_code) as sites,
        count(distinct month) as months,
        sum(consumption_kwh) as kwh
    from {{ ref('stg_electricity') }}
    group by 1
),

month_missing_findings as (
    select
        'electricity.month_missing' as check_key,
        m.company_code,
        cast(null as varchar) as match_key,
        cast(null as integer) as evidence_lines,
        cast(
            c.kwh / (c.sites * c.months) * m.missing_site_months
            as double
        ) as evidence_quantity,
        'kWh' as evidence_quantity_unit,
        cast(null as double) as evidence_amount_eur,
        cast(null as varchar) as evidence_amount_basis,
        cast(
            c.kwh / (c.sites * c.months) * m.missing_site_months
            * p.electricity_factor_kg_per_kwh / 1000
            as double
        ) as impact_tco2e,
        cast(null as double) as impact_eur,
        cast(m.missing_site_months as varchar) || ' site(s)-mois sans relevé.' as proof_extra,
        cast(null as varchar) as source_file,
        cast(null as integer) as source_row
    from missing_months m
    join electricity_coverage c on m.company_code = c.company_code
    cross join params p
),

exclusion_metrics as (
    select
        company_code,
        exclusion_reason,
        count(*) as evidence_lines,
        case
            when exclusion_reason = 'compte_non_mappe' then null
            else sum(activity_value)
        end as evidence_quantity,
        min(activity_unit) as evidence_quantity_unit,
        sum(amount_source_eur) as evidence_amount_eur,
        min(amount_source_basis) as evidence_amount_basis,
        sum(tco2e_non_compte) as tco2e_non_compte,
        min(source_file) as source_file,
        min(source_row) as source_row
    from {{ ref('fct_exclusions') }}
    where exclusion_reason not in ('couvert_par_physique', 'hors_perimetre')
    group by 1, 2
),

gwp_exclusion_metrics as (
    select
        e.company_code,
        'gwp_inconnu' as exclusion_reason,
        coalesce(nullif(trim(r.fluid_code), ''), 'empty') as match_key,
        count(*) as evidence_lines,
        sum(e.activity_value) as evidence_quantity,
        'kg' as evidence_quantity_unit,
        cast(null as double) as evidence_amount_eur,
        cast(null as varchar) as evidence_amount_basis,
        cast(null as double) as tco2e_non_compte,
        min(e.source_file) as source_file,
        min(e.source_row) as source_row
    from {{ ref('fct_exclusions') }} e
    join {{ ref('stg_refrigerants') }} r
      on e.company_code = r.company_code
     and e.source_id = r.source_id
     and e.source_row = r.source_row
    where e.exclusion_reason = 'gwp_inconnu'
    group by 1, 2, 3
),

exclusion_findings_raw as (
    select
        'exclusion.' || exclusion_reason as check_key,
        company_code,
        cast(null as varchar) as match_key,
        evidence_lines,
        evidence_quantity,
        evidence_quantity_unit,
        evidence_amount_eur,
        evidence_amount_basis,
        case
            when exclusion_reason in ('doublon_exact', 'billet_annule')
                then tco2e_non_compte
            when exclusion_reason = 'non_combustible'
                then evidence_quantity
                    * (select gazole_factor_kg_per_l from params) / 1000
        end as impact_tco2e,
        evidence_amount_eur as impact_eur,
        cast(null as varchar) as proof_extra,
        source_file,
        source_row
    from exclusion_metrics
    where exclusion_reason <> 'gwp_inconnu'

    union all

    select
        'exclusion.gwp_inconnu' as check_key,
        company_code,
        match_key,
        evidence_lines,
        evidence_quantity,
        evidence_quantity_unit,
        evidence_amount_eur,
        evidence_amount_basis,
        cast(null as double) as impact_tco2e,
        cast(null as double) as impact_eur,
        cast(null as varchar) as proof_extra,
        source_file,
        source_row
    from gwp_exclusion_metrics
),

flag_metrics as (
    select
        company_code,
        quality_flag,
        count(*) as evidence_lines,
        case
            when quality_flag = 'montant_negatif' then null
            else sum(activity_value)
        end as evidence_quantity,
        min(activity_unit) as evidence_quantity_unit,
        case
            when quality_flag in (
                'regularisation',
                'releve_estime',
                'produit_a_confirmer',
                'litres_estimes',
                'montant_negatif'
            ) then sum(amount_ht_eur)
            else sum(amount_source_eur)
        end as evidence_amount_eur,
        case
            when quality_flag in (
                'regularisation',
                'releve_estime',
                'produit_a_confirmer',
                'litres_estimes',
                'montant_negatif'
            ) then 'HT'
            else 'TTC'
        end as evidence_amount_basis,
        sum(tco2e) as tco2e,
        min(source_file) as source_file,
        min(source_row) as source_row
    from {{ ref('fct_emissions') }}
    where quality_flag in (
        'regularisation',
        'releve_estime',
        'produit_a_confirmer',
        'aller_simple_a_confirmer',
        'litres_estimes',
        'montant_negatif'
    )
    group by 1, 2
),

flag_findings as (
    select
        'quality_flag.' || quality_flag as check_key,
        company_code,
        cast(null as varchar) as match_key,
        evidence_lines,
        evidence_quantity,
        evidence_quantity_unit,
        evidence_amount_eur,
        evidence_amount_basis,
        tco2e as impact_tco2e,
        case
            when quality_flag = 'montant_negatif' then evidence_amount_eur
        end as impact_eur,
        cast(null as varchar) as proof_extra,
        source_file,
        source_row
    from flag_metrics
),

gap_findings as (
    select
        'gap.electricity_fec' as check_key,
        company_code,
        cast(null as varchar) as match_key,
        cast(null as integer) as evidence_lines,
        cast(null as double) as evidence_quantity,
        cast(null as varchar) as evidence_quantity_unit,
        abs(gap_eur) as evidence_amount_eur,
        'HT' as evidence_amount_basis,
        abs(gap_eur)
            / p.electricity_price_ht_eur_per_kwh
            * p.electricity_factor_kg_per_kwh
            / 1000 as impact_tco2e,
        abs(gap_eur) as impact_eur,
        cast(null as varchar) as proof_extra,
        cast(null as varchar) as source_file,
        cast(null as integer) as source_row
    from electricity_gaps
    cross join params p
    where abs(gap_eur) > 1

    union all

    select
        'gap.fuel_fec' as check_key,
        company_code,
        cast(null as varchar) as match_key,
        cast(null as integer) as evidence_lines,
        cast(null as double) as evidence_quantity,
        cast(null as varchar) as evidence_quantity_unit,
        abs(gap_eur) as evidence_amount_eur,
        'HT' as evidence_amount_basis,
        abs(gap_eur)
            / p.gazole_price_ttc_eur_per_l
            * p.gazole_factor_kg_per_l
            / 1000 as impact_tco2e,
        abs(gap_eur) as impact_eur,
        cast(null as varchar) as proof_extra,
        cast(null as varchar) as source_file,
        cast(null as integer) as source_row
    from fuel_gaps
    cross join params p
    where abs(gap_eur) > 1
),

vehicle_not_in_registry as (
    select
        f.company_code,
        count(distinct f.vehicle_id) as vehicles,
        min(f.source_file) as source_file,
        min(f.source_row) as source_row
    from {{ ref('stg_fuel') }} f
    left join {{ ref('stg_vehicles') }} v
      on f.company_code = v.company_code
     and f.vehicle_id = v.vehicle_id
    where f.vehicle_id is not null
      and v.vehicle_id is null
    group by f.company_code
),

card_without_vehicle as (
    select
        company_code,
        count(distinct card_id) as cards,
        min(source_file) as source_file,
        min(source_row) as source_row
    from {{ ref('stg_fuel') }}
    where vehicle_id is null
    group by company_code
),

reference_findings as (
    select
        'fuel.vehicle_not_in_registry' as check_key,
        company_code,
        cast(null as varchar) as match_key,
        cast(null as integer) as evidence_lines,
        cast(vehicles as double) as evidence_quantity,
        'véhicule(s)' as evidence_quantity_unit,
        cast(null as double) as evidence_amount_eur,
        cast(null as varchar) as evidence_amount_basis,
        cast(null as double) as impact_tco2e,
        cast(null as double) as impact_eur,
        cast(null as varchar) as proof_extra,
        source_file,
        source_row
    from vehicle_not_in_registry

    union all

    select
        'fuel.card_without_vehicle' as check_key,
        company_code,
        cast(null as varchar) as match_key,
        cast(null as integer) as evidence_lines,
        cast(cards as double) as evidence_quantity,
        'carte(s)' as evidence_quantity_unit,
        cast(null as double) as evidence_amount_eur,
        cast(null as varchar) as evidence_amount_basis,
        cast(null as double) as impact_tco2e,
        cast(null as double) as impact_eur,
        cast(null as varchar) as proof_extra,
        source_file,
        source_row
    from card_without_vehicle
),

mwh_findings as (
    select
        'electricity.unit_mwh' as check_key,
        e.company_code,
        cast(null as varchar) as match_key,
        count(*) as evidence_lines,
        sum(e.consumption_kwh) as evidence_quantity,
        'kWh' as evidence_quantity_unit,
        sum(e.amount_ht_eur) as evidence_amount_eur,
        'HT' as evidence_amount_basis,
        sum(e.consumption_kwh) * p.electricity_factor_kg_per_kwh / 1000 as impact_tco2e,
        cast(null as double) as impact_eur,
        'Unités source : ' || string_agg(distinct e.unit_raw, ', ') || '.' as proof_extra,
        min(e.source_file) as source_file,
        min(e.source_row) as source_row
    from {{ ref('stg_electricity') }} e
    cross join params p
    where e.unit_raw = 'MWh'
    group by e.company_code, p.electricity_factor_kg_per_kwh
),

vac_fuel as (
    select
        source_id,
        count(*) as lines,
        sum(quantity_l) as litres
    from {{ ref('stg_fuel') }}
    where company_code = 'VAC'
      and source_id in ('fuel_s1', 'fuel_s2')
    group by source_id
),

schema_drift as (
    select
        'fuel.schema_drift' as check_key,
        'VAC' as company_code,
        cast(null as varchar) as match_key,
        sum(v.lines) as evidence_lines,
        sum(v.litres) as evidence_quantity,
        'L' as evidence_quantity_unit,
        (
            select sum(amount_ttc_eur)
            from {{ ref('stg_fuel') }}
            where company_code = 'VAC'
        ) as evidence_amount_eur,
        'TTC' as evidence_amount_basis,
        sum(v.litres) * p.gazole_factor_kg_per_l / 1000 as impact_tco2e,
        cast(null as double) as impact_eur,
        'S1 : '
            || max(case when v.source_id = 'fuel_s1' then v.lines end)
            || ' lignes / '
            || round(max(case when v.source_id = 'fuel_s1' then v.litres end), 2)
            || ' L ; S2 : '
            || max(case when v.source_id = 'fuel_s2' then v.lines end)
            || ' lignes / '
            || round(max(case when v.source_id = 'fuel_s2' then v.litres end), 2)
            || ' L.' as proof_extra,
        (
            select min(source_file)
            from {{ ref('stg_fuel') }}
            where company_code = 'VAC'
        ) as source_file,
        (
            select min(source_row)
            from {{ ref('stg_fuel') }}
            where company_code = 'VAC'
        ) as source_row
    from vac_fuel v
    cross join params p
    group by p.gazole_factor_kg_per_l
),

unit_findings as (
    select * from mwh_findings
    union all
    select * from schema_drift
),

mapping_watchlist(company_code, match_key, account_prefix) as (
    values
        ('FAN', '6011000,6021000', '6011000'),
        ('FAN', '6011000,6021000', '6021000'),
        ('FAN', '62512000', '62512000'),
        ('VAC', '6011000,6022000', '6011000'),
        ('VAC', '6011000,6022000', '6022000'),
        ('VAC', '6231000', '6231000')
),

mapping_metrics as (
    select
        w.company_code,
        w.match_key,
        count(*) as evidence_lines,
        sum(m.amount_ht_eur) as evidence_amount_eur,
        sum(m.tco2e) as impact_tco2e,
        min(m.source_file) as source_file,
        min(m.source_row) as source_row
    from mapping_watchlist w
    join {{ ref('int_fec_monetaire') }} m
      on m.company_code = w.company_code
     and starts_with(m.source_reference, w.account_prefix)
    group by 1, 2
),

mapping_findings as (
    select
        'mapping.account_to_confirm' as check_key,
        company_code,
        match_key,
        evidence_lines,
        cast(null as double) as evidence_quantity,
        cast(null as varchar) as evidence_quantity_unit,
        evidence_amount_eur,
        'HT' as evidence_amount_basis,
        impact_tco2e,
        cast(null as double) as impact_eur,
        cast(null as varchar) as proof_extra,
        source_file,
        source_row
    from mapping_metrics
),

fec_ht_findings as (
    select
        'fec.ht_assumption' as check_key,
        company_code,
        cast(null as varchar) as match_key,
        count(*) as evidence_lines,
        cast(null as double) as evidence_quantity,
        cast(null as varchar) as evidence_quantity_unit,
        cast(null as double) as evidence_amount_eur,
        cast(null as varchar) as evidence_amount_basis,
        cast(null as double) as impact_tco2e,
        cast(null as double) as impact_eur,
        cast(null as varchar) as proof_extra,
        min(source_file) as source_file,
        min(source_row) as source_row
    from {{ ref('stg_fec') }}
    group by company_code
),

fec_cet_findings as (
    select
        'fec.cet_out_of_scope' as check_key,
        company_code,
        cast(null as varchar) as match_key,
        count(*) as evidence_lines,
        cast(null as double) as evidence_quantity,
        cast(null as varchar) as evidence_quantity_unit,
        sum(debit - credit) as evidence_amount_eur,
        'HT' as evidence_amount_basis,
        cast(null as double) as impact_tco2e,
        sum(debit - credit) as impact_eur,
        cast(null as varchar) as proof_extra,
        min(source_file) as source_file,
        min(source_row) as source_row
    from {{ ref('stg_fec') }}
    where account = '6351100'
    group by company_code
),

unbalanced_entries as (
    select
        f.company_code,
        f.source_id,
        f.entry_id,
        f.source_row,
        f.entry_balance_eur,
        f.source_file,
        m.ratio_kgco2e_par_keur,
        row_number() over (
            partition by f.company_code, f.source_id, f.source_row
            order by length(m.prefix) desc nulls last
        ) as mapping_rank
    from {{ ref('stg_fec') }} f
    left join {{ ref('ref_account_mapping') }} m
      on starts_with(f.account, m.prefix)
    where abs(f.entry_balance_eur) > 0.005
),

unbalanced_entry_totals as (
    select
        company_code,
        source_id,
        entry_id,
        count(*) as lines,
        max(abs(entry_balance_eur)) as balance_eur,
        max(coalesce(ratio_kgco2e_par_keur, 0)) as ratio_kgco2e_par_keur,
        min(source_file) as source_file,
        min(source_row) as source_row
    from unbalanced_entries
    where mapping_rank = 1
    group by 1, 2, 3
),

fec_balance_findings as (
    select
        'fec.unbalanced_entry' as check_key,
        company_code,
        cast(null as varchar) as match_key,
        sum(lines) as evidence_lines,
        cast(null as double) as evidence_quantity,
        cast(null as varchar) as evidence_quantity_unit,
        sum(balance_eur) as evidence_amount_eur,
        'HT' as evidence_amount_basis,
        sum(balance_eur * ratio_kgco2e_par_keur / 1000000) as impact_tco2e,
        sum(balance_eur) as impact_eur,
        cast(null as varchar) as proof_extra,
        min(source_file) as source_file,
        min(source_row) as source_row
    from unbalanced_entry_totals
    group by company_code
),

fuel_outlier_findings as (
    select
        'fuel.quantity_above_tank' as check_key,
        f.company_code,
        cast(null as varchar) as match_key,
        count(*) as evidence_lines,
        sum(f.quantity_l) as evidence_quantity,
        'L' as evidence_quantity_unit,
        cast(null as double) as evidence_amount_eur,
        cast(null as varchar) as evidence_amount_basis,
        sum(
            (f.quantity_l - v.tank_capacity_l)
            * p.gazole_factor_kg_per_l
            / 1000
        ) as impact_tco2e,
        cast(null as double) as impact_eur,
        'Véhicule '
            || string_agg(f.vehicle_id, ', ')
            || ' ; dépassement '
            || round(sum(f.quantity_l - v.tank_capacity_l), 2)
            || ' L.' as proof_extra,
        min(f.source_file) as source_file,
        min(f.source_row) as source_row
    from {{ ref('stg_fuel') }} f
    join {{ ref('stg_vehicles') }} v
      on f.company_code = v.company_code
     and f.vehicle_id = v.vehicle_id
    cross join params p
    where f.quantity_l > v.tank_capacity_l
    group by f.company_code, p.gazole_factor_kg_per_l
),

cabin_findings as (
    select
        'flights.cabin_class_standard_factor' as check_key,
        'ALL' as company_code,
        cast(null as varchar) as match_key,
        count(*) as evidence_lines,
        cast(null as double) as evidence_quantity,
        cast(null as varchar) as evidence_quantity_unit,
        sum(amount_source_eur) as evidence_amount_eur,
        'TTC' as evidence_amount_basis,
        sum(tco2e) as impact_tco2e,
        cast(null as double) as impact_eur,
        cast(null as varchar) as proof_extra,
        min(source_file) as source_file,
        min(source_row) as source_row
    from {{ ref('fct_emissions') }}
    where quality_flag = 'classe_affaires_facteur_standard'
),

all_findings as (
    select * from electricity_site_findings
    union all
    select * from refrigerant_site_findings
    union all
    select * from month_missing_findings
    union all
    select * from exclusion_findings_raw
    union all
    select * from flag_findings
    union all
    select * from gap_findings
    union all
    select * from reference_findings
    union all
    select * from unit_findings
    union all
    select * from mapping_findings
    union all
    select * from fec_ht_findings
    union all
    select * from fec_cet_findings
    union all
    select * from fec_balance_findings
    union all
    select * from fuel_outlier_findings
    union all
    select * from cabin_findings
)

select
    check_key,
    company_code,
    match_key,
    evidence_lines,
    evidence_quantity,
    evidence_quantity_unit,
    evidence_amount_eur,
    evidence_amount_basis,
    impact_tco2e,
    impact_eur,
    proof_extra,
    source_file,
    source_row
from all_findings
