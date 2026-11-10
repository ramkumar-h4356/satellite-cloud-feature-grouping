
from pathlib import Path
import xarray as xr
import pandas as pd
import re

BASE_DIR = Path(__file__).resolve().parent

files = sorted(BASE_DIR.glob("nices_cm4_*/*.nc"))

if not files:
    raise FileNotFoundError("No NetCDF files found.")

daily_data = []
all_times = set()

# Step 1: Extract observation times from every NetCDF file
for file_path in files:
    print(f"Inspecting: {file_path.parent.name}")

    try:
        with xr.open_dataset(
            file_path,
            engine="netcdf4",
            decode_cf=False,
            mask_and_scale=False
        ) as ds:

            cloud_times = {
                match.group(1)
                for name in ds.data_vars
                if (match := re.fullmatch(r"cloud_mask_(\d{4})", name))
            }

            flag_times = {
                match.group(1)
                for name in ds.data_vars
                if (match := re.fullmatch(r"flag_(\d{4})", name))
            }

            all_times.update(cloud_times)
            all_times.update(flag_times)

            daily_data.append({
                "date": file_path.parent.name.replace("nices_cm4_", ""),
                "cloud_times": cloud_times,
                "flag_times": flag_times
            })

    except Exception as error:
        print(f"ERROR in {file_path}: {error}")

# Step 2: Sort observation times
all_times = sorted(all_times)
all_times_set = set(all_times)

# Step 3: Construct daily observation availability matrix
rows = []

for day in daily_data:

    missing_cloud = sorted(
        all_times_set - day["cloud_times"]
    )

    missing_flag = sorted(
        all_times_set - day["flag_times"]
    )

    mismatches = sorted(
        day["cloud_times"] ^ day["flag_times"]
    )

    row = {
        "date": day["date"],
        "cloud_observation_count": len(day["cloud_times"]),
        "flag_observation_count": len(day["flag_times"]),
        "missing_cloud_times": ",".join(missing_cloud),
        "missing_flag_times": ",".join(missing_flag),
        "cloud_flag_mismatches": ",".join(mismatches)
    }

    # 1 = variable exists, 0 = variable absent
    for time in all_times:
        row[time] = int(time in day["cloud_times"])

    rows.append(row)

# Step 4: Create DataFrame
df = pd.DataFrame(rows)

# Step 5: Save observation availability report
output_file = BASE_DIR / "observation_availability.csv"

df.to_csv(output_file, index=False)

# Step 6: Display results
print("\n" + "=" * 60)
print("OBSERVATION AVAILABILITY AUDIT")
print("=" * 60)

print("\nTotal NetCDF files inspected:", len(daily_data))
print("Unique observation times:", len(all_times))
print("Observation times:", all_times)

print("\nDAILY OBSERVATION COUNTS")
print("-" * 60)

print(
    df[
        [
            "date",
            "cloud_observation_count",
            "flag_observation_count"
        ]
    ].to_string(index=False)
)

print("\nCLOUD-FLAG MISMATCHES")
print("-" * 60)

mismatch_found = False

for day in daily_data:
    mismatches = sorted(
        day["cloud_times"] ^ day["flag_times"]
    )

    if mismatches:
        mismatch_found = True
        print(day["date"], ":", mismatches)

if not mismatch_found:
    print("No cloud-mask/flag variable mismatches found.")

print("\nOBSERVATION AVAILABILITY MATRIX")
print("-" * 60)

availability_columns = ["date"] + all_times

print(
    df[availability_columns].to_string(index=False)
)

print("\nReport saved successfully:")
print(output_file)
