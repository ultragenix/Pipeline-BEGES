select
    prefixe::varchar as prefix,
    libelle,
    poste,
    try_cast(scope as integer) as scope,
    try_cast(ratio_kgco2e_par_keur as double) as ratio_kgco2e_par_keur,
    nullif(remplace_par, '') as replaced_by,
    nullif(type, '') as mapping_type
from read_csv_auto(
    '{{ env_var("BEGES_CONFIG_DIR") }}/account_mapping.csv',
    header = true,
    all_varchar = true
)
