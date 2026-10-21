select
    company_code || ':' || source_id || ':' || reason_code as quarantine_key,
    company_code,
    source_id,
    reason_code,
    count(*) as nb_lignes,
    min(quarantined_at) as first_seen_at,
    max(quarantined_at) as last_seen_at
from {{ source('raw', 'quarantine') }}
group by 1, 2, 3, 4
