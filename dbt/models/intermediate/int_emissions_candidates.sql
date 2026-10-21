select * from {{ ref('int_fec_monetaire') }}
union all
select * from {{ ref('int_electricity_physique') }}
union all
select * from {{ ref('int_fuel_physique') }}
union all
select * from {{ ref('int_refrigerants_physique') }}
union all
select * from {{ ref('int_flights_physique') }}
