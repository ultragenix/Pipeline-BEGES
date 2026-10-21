with events as (
    select
        company_code,
        'fec' as source_type,
        entry_date as event_date
    from {{ source('raw', 'fec') }}

    union all

    select
        company_code,
        'electricity' as source_type,
        month as event_date
    from {{ source('raw', 'electricity') }}

    union all

    select
        company_code,
        'fuel' as source_type,
        transaction_date as event_date
    from {{ source('raw', 'fuel') }}

    union all

    select
        company_code,
        'refrigerants' as source_type,
        intervention_date as event_date
    from {{ source('raw', 'refrigerants') }}

    union all

    select
        company_code,
        'flights' as source_type,
        emission_date as event_date
    from {{ source('raw', 'flights') }}

    union all

    select
        company_code,
        'vehicles' as source_type,
        cast(null as date) as event_date
    from {{ source('raw', 'vehicles') }}
),

aggregated as (
    select
        company_code || ':' || source_type as freshness_key,
        company_code,
        source_type,
        min(event_date) as min_date,
        max(event_date) as max_date,
        count(*) as nb_lignes,
        count(distinct date_trunc('month', event_date)) as nb_mois
    from events
    group by 1, 2, 3
)

select * from aggregated
