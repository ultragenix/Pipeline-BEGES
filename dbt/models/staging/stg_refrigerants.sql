select
    *,
    upper(trim(fluid_code)) as fluid_code_norm,
    recharge_kg > nominal_charge_kg as recharge_above_charge
from {{ source('raw', 'refrigerants') }}
