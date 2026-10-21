with source as (
    select * from {{ ref('stg_flights') }}
),

airports as (
    select iata, latitude, longitude
    from {{ ref('ref_airports') }}
),

params as (
    select distance_correction_km, vat_rate
    from {{ ref('ref_parameters') }}
),

bands as (
    select code, value, max_km
    from {{ ref('ref_emission_factors') }}
    where category = 'flight'
),

located as (
    select
        s.*,
        o.latitude as origin_latitude,
        o.longitude as origin_longitude,
        d.latitude as destination_latitude,
        d.longitude as destination_longitude
    from source s
    left join airports o on s.origin_iata = o.iata
    left join airports d on s.destination_iata = d.iata
),

distances as (
    select
        l.*,
        case
            when l.origin_latitude is not null
                and l.destination_latitude is not null
            then {{ haversine_km('l.origin_latitude', 'l.origin_longitude', 'l.destination_latitude', 'l.destination_longitude') }}
                + p.distance_correction_km
        end as one_way_km,
        p.vat_rate
    from located l
    cross join params p
),

banded as (
    select
        d.*,
        b.code as band_code,
        b.value as emission_factor,
        row_number() over (
            partition by d.company_code, d.source_id, d.source_row
            order by b.max_km nulls last
        ) as band_rank
    from distances d
    left join bands b
        on d.one_way_km is not null
        and (b.max_km is null or d.one_way_km < b.max_km)
),

flagged as (
    select
        *,
        case
            when one_way_km is null then null
            when trip_type = 'AR' then one_way_km * 2
            else one_way_km
        end as distance_km,
        (
            not is_exact_duplicate
            and not is_cancelled
            and one_way_km is not null
            and emission_factor is not null
        ) as is_included,
        case
            when is_exact_duplicate then 'doublon_exact'
            when is_cancelled then 'billet_annule'
            when destination_iata is null then 'destination_manquante'
            when one_way_km is null then 'aeroport_inconnu'
            when emission_factor is null then 'facteur_absent'
        end as exclusion_reason
    from banded
    where band_rank = 1
)

select
    company_code || ':flights:' || source_id || ':' || source_row
        as emission_id,
    company_code,
    'flights' as source_type,
    source_id,
    source_file,
    source_sheet,
    source_row,
    ingestion_id,
    ingested_at,
    3 as scope,
    'Déplacements professionnels' as poste,
    'Billets d''avion' as activity,
    case
        when distance_km is not null and emission_factor is not null
            then 'physique'
        else 'non_calcule'
    end as method,
    distance_km as activity_value,
    'passager.km' as activity_unit,
    emission_factor,
    'kgCO2e/passager.km' as emission_factor_unit,
    case
        when distance_km is not null and emission_factor is not null
        then distance_km * emission_factor / 1000
    end as tco2e,
    amount_ttc_eur as amount_source_eur,
    'TTC' as amount_source_basis,
    amount_ttc_eur / (1 + vat_rate) as amount_ht_eur,
    is_included,
    exclusion_reason,
    case
        when trip_type = 'AS' then 'aller_simple_a_confirmer'
        when cabin_class = 'Affaires' then 'classe_affaires_facteur_standard'
    end as quality_flag,
    ticket_id as source_reference
from flagged
