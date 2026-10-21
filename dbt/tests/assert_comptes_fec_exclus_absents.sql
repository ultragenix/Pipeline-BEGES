select
    f.company_code,
    f.source_id,
    f.source_row
from {{ ref('int_fec_monetaire') }} f
where not f.is_included
    and exists (
        select 1
        from {{ ref('fct_emissions') }} e
        where e.company_code = f.company_code
            and e.source_type = 'fec'
            and e.source_id = f.source_id
            and e.source_row = f.source_row
    )
