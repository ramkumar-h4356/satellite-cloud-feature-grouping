
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import xarray as xr

BASE_DIR = Path(__file__).parent
MASK_FILE = BASE_DIR / "india_mask_october.npz"

# Load India geographical mask
india_mask = np.load(MASK_FILE)["india_mask"]

# Expected raw values from the current metadata
CLOUD_CODES = [0, 1, 2, -127]
FLAG_CODES = [-1, 1, 2, 3, 4, -127]

daily_folders = sorted(BASE_DIR.glob("nices_cm4_*"))

observation_results = []
missing_pairs = []

def count_values(array):
    values, counts = np.unique(array, return_counts=True)
    return dict(zip(values.tolist(), counts.tolist()))

for folder in daily_folders:

    netcdf_files = list(folder.glob("INS3S*.nc"))

    if not netcdf_files:
        print(f"Skipping {folder.name}: no NetCDF file")
        continue

    file = netcdf_files[0]

    print(f"\nInspecting {folder.name}...")

    with xr.open_dataset(
        file,
        decode_cf=False,
        mask_and_scale=False
    ) as ds:

        cloud_variables = sorted(
            name for name in ds.data_vars
            if name.startswith("cloud_mask_")
        )

        for cloud_name in cloud_variables:

            time_label = cloud_name.replace("cloud_mask_", "")
            flag_name = f"flag_{time_label}"

            if flag_name not in ds:
                missing_pairs.append({
                    "date": folder.name,
                    "time": time_label,
                    "missing_variable": flag_name
                })
                continue

            cloud_var = ds[cloud_name]
            flag_var = ds[flag_name]

            cloud = cloud_var.transpose(
                "latitude", "longitude"
            ).values

            flag = flag_var.transpose(
                "latitude", "longitude"
            ).values

            if cloud.shape != india_mask.shape:
                raise ValueError(
                    f"Cloud shape mismatch in {folder.name}, "
                    f"{cloud_name}: {cloud.shape}"
                )

            if flag.shape != india_mask.shape:
                raise ValueError(
                    f"Flag shape mismatch in {folder.name}, "
                    f"{flag_name}: {flag.shape}"
                )

            # Extract India-only values
            cloud_india = cloud[india_mask]
            flag_india = flag[india_mask]

            cloud_counts = count_values(cloud_india)
            flag_counts = count_values(flag_india)

            # Cloud-mask and flag relationship checks
            cloudy = cloud_india == 1
            clear = cloud_india == 0
            uncertain = cloud_india == 2

            flag_missing = np.isin(flag_india, [-1, -127])
            flag_valid = np.isin(flag_india, [1, 2, 3, 4])

            cloudy_missing_flag = np.count_nonzero(
                cloudy & flag_missing
            )

            clear_with_valid_flag = np.count_nonzero(
                clear & flag_valid
            )

            uncertain_flag_not_minus1 = np.count_nonzero(
                uncertain & (flag_india != -1)
            )

            unexpected_cloud = {
                value: count
                for value, count in cloud_counts.items()
                if value not in CLOUD_CODES
            }

            unexpected_flag = {
                value: count
                for value, count in flag_counts.items()
                if value not in FLAG_CODES
            }

            row = {
                "date": folder.name,
                "time": time_label,
                "india_pixels": len(cloud_india),

                "cloud_0": cloud_counts.get(0, 0),
                "cloud_1": cloud_counts.get(1, 0),
                "cloud_2": cloud_counts.get(2, 0),
                "cloud_minus127": cloud_counts.get(-127, 0),

                "flag_minus1": flag_counts.get(-1, 0),
                "flag_1": flag_counts.get(1, 0),
                "flag_2": flag_counts.get(2, 0),
                "flag_3": flag_counts.get(3, 0),
                "flag_4": flag_counts.get(4, 0),
                "flag_minus127": flag_counts.get(-127, 0),

                "cloudy_missing_flag": cloudy_missing_flag,
                "clear_with_valid_flag": clear_with_valid_flag,
                "uncertain_flag_not_minus1": uncertain_flag_not_minus1,

                "unexpected_cloud_values": str(unexpected_cloud),
                "unexpected_flag_values": str(unexpected_flag)
            }

            observation_results.append(row)

# Create reports
report = pd.DataFrame(observation_results)

observation_file = BASE_DIR / "all_days_observation_audit.csv"
report.to_csv(observation_file, index=False)

missing_file = BASE_DIR / "missing_cloud_flag_pairs.csv"
pd.DataFrame(missing_pairs).to_csv(missing_file, index=False)

# Aggregate counts across all dates and times
count_columns = [
    column for column in report.columns
    if column.startswith(("cloud_", "flag_"))
    and column not in [
        "unexpected_cloud_values",
        "unexpected_flag_values"
    ]
]

aggregate = report[count_columns].sum()

summary_file = BASE_DIR / "all_days_aggregate_audit.csv"

pd.DataFrame({
    "metric": aggregate.index,
    "count": aggregate.values
}).to_csv(summary_file, index=False)

# Print summary
print("\n" + "=" * 55)
print("ALL DAYS INDIA CLOUD-FLAG AUDIT SUMMARY")
print("=" * 55)

print("Daily files inspected:", report["date"].nunique())
print("Observation pairs inspected:", len(report))
print("Missing cloud-flag pairs:", len(missing_pairs))

print("\nAGGREGATE PIXEL-OBSERVATION COUNTS")

for metric, count in aggregate.items():
    print(f"{metric}: {count}")

print("\nRELATIONSHIP CHECKS")

print(
    "Cloudy pixels with missing flags:",
    report["cloudy_missing_flag"].sum()
)

print(
    "Clear pixels with valid flags:",
    report["clear_with_valid_flag"].sum()
)

print(
    "Cloud value 2 pixels with flag other than -1:",
    report["uncertain_flag_not_minus1"].sum()
)

print("\nUnexpected cloud values:")
print(
    report.loc[
        report["unexpected_cloud_values"] != "{}",
        ["date", "time", "unexpected_cloud_values"]
    ].to_string(index=False)
)

print("\nUnexpected flag values:")
print(
    report.loc[
        report["unexpected_flag_values"] != "{}",
        ["date", "time", "unexpected_flag_values"]
    ].to_string(index=False)
)

print("\nREPORTS SAVED")
print(observation_file)
print(missing_file)
print(summary_file)
