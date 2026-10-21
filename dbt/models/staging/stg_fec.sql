with source as (
    select * from {{ source('raw', 'fec') }}
)

select
    company_code,
    source_id,
    source_file,
    source_sheet,
    source_row,
    ingestion_id,
    ingested_at,
    entry_id,
    entry_date,
    account,
    account_label,
    supplier_id,
    supplier_label,
    piece_ref,
    piece_date,
    label,
    debit,
    credit,
    valid_date,
    debit - credit as amount_ht_eur,
    left(account, 1) as account_class,
    date_part('year', entry_date) as exercise_year,
    sum(debit) over (
        partition by company_code, source_id, entry_id
    ) as entry_debit_eur,
    sum(credit) over (
        partition by company_code, source_id, entry_id
    ) as entry_credit_eur,
    sum(debit - credit) over (
        partition by company_code, source_id, entry_id
    ) as entry_balance_eur
from source
