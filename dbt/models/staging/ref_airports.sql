select
    upper(iata) as iata,
    name,
    city,
    country,
    try_cast(latitude as double) as latitude,
    try_cast(longitude as double) as longitude
from read_csv_auto(
    '{{ env_var("BEGES_CONFIG_DIR") }}/airports.csv',
    header = true,
    all_varchar = true
)
