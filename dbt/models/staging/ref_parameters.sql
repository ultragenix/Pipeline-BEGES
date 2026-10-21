select
    max(
        case
            when category = 'electricity' and code = 'ELEC_REUNION'
                then value
        end
    ) as electricity_factor_kg_per_kwh,
    max(
        case when category = 'fuel' and code = 'GAZOLE' then value end
    ) as gazole_factor_kg_per_l,
    max(
        case when category = 'fuel' and code = 'SP95' then value end
    ) as sp95_factor_kg_per_l,
    max(
        case
            when category = 'price' and code = 'gazole_ttc_eur_per_l'
                then value
        end
    ) as gazole_price_ttc_eur_per_l,
    max(
        case
            when category = 'price' and code = 'sp95_ttc_eur_per_l'
                then value
        end
    ) as sp95_price_ttc_eur_per_l,
    max(
        case when category = 'price' and code = 'vat_rate' then value end
    ) as vat_rate,
    max(
        case
            when category = 'flight_param' and code = 'distance_correction_km'
                then value
        end
    ) as distance_correction_km
from {{ ref('ref_emission_factors') }}
