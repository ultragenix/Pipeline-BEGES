with source as (
    select * from {{ source('raw', 'fuel') }}
),

classified as (
    select
        *,
        case upper(trim(product_raw))
            when 'GAZOLE' then 'GAZOLE'
            when 'B7' then 'GAZOLE'
            when 'GO' then 'GAZOLE'
            when 'DIESEL' then 'GAZOLE'
            when 'SP95' then 'SP95'
            when 'ADBLUE' then 'NON_CARBURANT'
            when 'PRODUIT 47' then 'INCONNU'
            else 'INCONNU'
        end as product_code,
        case upper(trim(product_raw))
            when 'B7' then 'a_confirmer'
            when 'GO' then 'a_confirmer'
            when 'DIESEL' then 'a_confirmer'
            when 'GAZOLE' then 'certain'
            when 'SP95' then 'certain'
            when 'ADBLUE' then 'certain'
            when 'PRODUIT 47' then 'certain'
            else 'inconnu'
        end as product_confidence
    from source
)

select * from classified
