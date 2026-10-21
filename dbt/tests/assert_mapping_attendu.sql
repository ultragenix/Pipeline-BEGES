select *
from {{ ref('int_fec_monetaire') }}
where
    (
        company_code = 'KAY'
        and source_reference = '6288000'
        and exclusion_reason is distinct from 'compte_non_mappe'
    )
    or (
        company_code = 'KAY'
        and source_reference = '6351100'
        and exclusion_reason is distinct from 'hors_perimetre'
    )
    or (
        company_code = 'KAY'
        and source_reference = '6061100'
        and (
            exclusion_reason is distinct from 'couvert_par_physique'
            or poste is distinct from 'Électricité'
        )
    )
    or (
        company_code = 'KAY'
        and source_reference = '6062200'
        and (
            exclusion_reason is distinct from 'couvert_par_physique'
            or poste is distinct from 'Combustion mobile'
        )
    )
    or (
        company_code = 'KAY'
        and source_reference = '6251100'
        and (
            exclusion_reason is distinct from 'couvert_par_physique'
            or poste is distinct from 'Déplacements professionnels'
        )
    )
    or (
        company_code = 'FAN'
        and source_reference = '6021000'
        and (poste is distinct from 'Achats de biens' or not is_included)
    )
    or (
        company_code = 'VAC'
        and source_reference = '6022000'
        and (poste is distinct from 'Achats de biens' or not is_included)
    )
    or (
        company_code = 'VAC'
        and source_reference = '6231000'
        and (poste is distinct from 'Achats de services' or not is_included)
    )
