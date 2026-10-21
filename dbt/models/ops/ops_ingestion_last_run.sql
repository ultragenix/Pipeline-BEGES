with ranked as (
    select
        *,
        row_number() over (
            partition by company_code, source_id
            order by finished_at desc
        ) as run_rank
    from {{ source('raw', 'ingestion_log') }}
)

select
    company_code || ':' || source_id as source_key,
    company_code,
    source_id,
    source_type,
    source_file,
    source_sheet,
    ingestion_id,
    rows_read,
    rows_loaded,
    rows_quarantined,
    status,
    error,
    duration_ms,
    started_at,
    finished_at
from ranked
where run_rank = 1
