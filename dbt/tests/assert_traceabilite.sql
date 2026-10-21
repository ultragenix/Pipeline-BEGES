select *
from {{ ref('fct_emissions') }}
where source_file is null
    or source_row is null
    or ingestion_id is null
    or source_id is null
    or source_type is null
