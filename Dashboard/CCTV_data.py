import pandas as pd
from pathlib import Path
import config

data_folder = Path(config.POLICE_CRIME_DATA)
files = list(data_folder.rglob("*-street.csv"))

df_list = []

for file in files:
    temp = pd.read_csv(file)
    temp["source_file"] = file.name
    df_list.append(temp)

raw_df = pd.concat(df_list, ignore_index=True)

severe_crimes = [
    "Violence and sexual offences",
    "Burglary",
    "Drugs",
    "Possession of weapons",
    "Robbery"
]

non_severe_df = raw_df[
    ~raw_df["Crime type"].isin(severe_crimes)
].copy()

non_severe_df = non_severe_df.dropna(subset=["LSOA code", "LSOA name"])

weak_outcomes = [
    "Investigation complete; no suspect identified",
    "Unable to prosecute suspect"
]

non_severe_df["is_unsolved"] = non_severe_df["Last outcome category"].isin(weak_outcomes)

df = non_severe_df.groupby(["LSOA code", "LSOA name"]).agg(
    unsolved_non_severe=("is_unsolved", "sum"),
    total_non_severe=("Crime type", "count")
).reset_index()

df = df.rename(columns={
    "LSOA code": "LSOA_ID",
    "LSOA name": "LSOA_NAME"
})


def assign_priority(row, non_suspect, non_severe_crime):
    unsolved = row["unsolved_non_severe"]
    frequency = row["total_non_severe"]

    if unsolved >= non_suspect:
        return 1

    elif unsolved > 0 and frequency >= non_severe_crime:
        return 2

    else:
        return 3


def priority_score(row):
    priority = row["priority_level"]
    unsolved_norm = row["unsolved_norm"]
    frequency_norm = row["frequency_norm"]

    if priority == 1:
        priority_num = 2.0
    elif priority == 2:
        priority_num = 1.0
    else:
        priority_num = 0.0

    score = (
            priority_num + 0.6 * unsolved_norm + 0.4 * frequency_norm
    )

    return score


def norm(column):
    if column.max() == column.min():
        return column * 0
    return (column - column.min()) / (column.max() - column.min())


ave_non_suspect = df["unsolved_non_severe"].mean()
ave_non_severe_crime = df["total_non_severe"].mean()

print("Average unsolved non-severe:", ave_non_suspect)
print("Average total non-severe:", ave_non_severe_crime)

df["priority_level"] = df.apply(
    assign_priority,
    axis=1,
    non_suspect=ave_non_suspect,
    non_severe_crime=ave_non_severe_crime
)

df["unsolved_norm"] = norm(df["unsolved_non_severe"])
df["frequency_norm"] = norm(df["total_non_severe"])

df["cctv_score"] = df.apply(priority_score, axis=1)

df = df.sort_values(by="cctv_score", ascending=False)

df["cctv_rank"] = range(1, len(df) + 1)

print(df.head())
df.to_csv(config.CCTV_PRIORITY_CSV, index=False)
