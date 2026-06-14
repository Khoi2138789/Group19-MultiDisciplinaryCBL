import duckdb
import pandas as pd
import os
import config

con = duckdb.connect(config.DUCKDB_DATABASE)
path = os.path.join(config.DATA_DIR, "**", "*-street.csv").replace('\\', '/')

query = f"""
    SELECT 
        Month,
        "LSOA code" AS LSOA_ID,
        SUM(
            CASE 
                WHEN TRIM("Crime type") = 'Violence and sexual offences' THEN 1058.556
                WHEN TRIM("Crime type") = 'Burglary' THEN 564.016
                WHEN TRIM("Crime type") = 'Drugs' THEN 666.678
                WHEN TRIM("Crime type") = 'Possession of weapons' THEN 1710.724
                WHEN TRIM("Crime type") = 'Robbery' THEN 993.551
                ELSE 0 
            END
        ) AS Total_CII_Score
    FROM read_csv_auto('{path}') 
    WHERE 
        "LSOA code" IS NOT NULL 
        AND "LSOA code" LIKE 'E%'
        AND Month BETWEEN '2023-01' AND '2026-03'
        AND TRIM("Crime type") IN (
            'Violence and sexual offences', 
            'Burglary', 
            'Drugs', 
            'Possession of weapons', 
            'Robbery'
        )
    GROUP BY 
        Month, 
        "LSOA code"
    ORDER BY 
        "LSOA code", 
        Month
"""


prophet_training_data = con.execute(query).df()
print(prophet_training_data.head())
print(prophet_training_data.tail())

prophet_training_data.to_csv(config.PROPHET_INPUT_CSV, index=False)

query_pcp = f"""
    SELECT 
        "LSOA code" AS LSOA_ID,
        TRIM("Crime type") AS Crime_Type,
        SUM(
            CASE 
                WHEN TRIM("Crime type") = 'Violence and sexual offences' THEN 1058.556
                WHEN TRIM("Crime type") = 'Burglary' THEN 564.016
                WHEN TRIM("Crime type") = 'Drugs' THEN 666.678
                WHEN TRIM("Crime type") = 'Possession of weapons' THEN 1710.724
                WHEN TRIM("Crime type") = 'Robbery' THEN 993.551
                ELSE 0 
            END
        ) AS Total_Intensity
    FROM read_csv_auto('{path}') 
    WHERE 
        "LSOA code" IS NOT NULL 
        AND "LSOA code" LIKE 'E%'
        AND Month BETWEEN '2023-01' AND '2026-03'
        AND TRIM("Crime type") IN (
            'Violence and sexual offences', 
            'Burglary', 
            'Drugs', 
            'Possession of weapons', 
            'Robbery'
        )
    GROUP BY 
        "LSOA code", 
        TRIM("Crime type")
"""

pcp_data = con.execute(query_pcp).df()
print(pcp_data.head())

pcp_data.to_csv(config.CRIME_TYPES_CSV, index=False)

con.close()