
from pathlib import Path
from datetime import date, timedelta
import xarray as xr
import csv
import json

BASE_DIR = Path(__file__).resolve().parent
START_DATE = date(2026, 10, 1)
END_DATE = date(2026, 11, 1)

summary_rows = []
variable_rows = []
audit_errors = []

def json_text(value):
    return json.dumps(value, default=str)

# Identify expected dates and available folders
expected_dates = set()
current = START_DATE

while current <= END_DATE:
    expected_dates.add(current.strftime("%Y%m%d"))
    current += timedelta(days=1)

folders = {
    folder.name.replace("nices_cm4_", "")
    for folder in BASE_DIR.iterdir()
    if folder.is_dir() and folder.name.startswith("nices_cm4_")
}

missing_dates = sorted(expected_dates - folders)
unexpected_dates = sorted(folders - expected_dates)

# Find and inspect NetCDF files
nc_files = sorted(BASE_DIR.glob("nices_cm4_*/ *.nc"))

# Correct glob pattern for NetCDF files
nc_files = sorted(BASE_DIR.glob("nices_cm4_*/*.nc"))

reference_schema = None
schema_differences = []

for file_path in nc_files:
    print(f"Inspecting: {file_path.parent.name}")

    try:
        with xr.open_dataset(
            file_path,
            engine="netcdf4",
            decode_cf=False,
            mask_and_scale=False
        ) as ds:

            dimensions = dict(ds.sizes)

            data_variables = list(ds.data_vars)
            coordinates = list(ds.coords)

            schema = {
                name: {
                    "dimensions": list(var.dims),
                    "dtype": str(var.dtype)
                }
                for name, var in ds.variables.items()
            }

            summary_rows.append({
                "date_folder": file_path.parent.name,
                "filename": file_path.name,
                "file_size_MB": round(file_path.stat().st_size / (1024 ** 2), 3),
                "dimensions": json_text(dimensions),
                "coordinate_variables": json_text(coordinates),
                "data_variable_count": len(data_variables),
                "data_variables": json_text(data_variables),
                "global_attributes": json_text(dict(ds.attrs))
            })

            for name, var in ds.variables.items():
                variable_rows.append({
                    "date_folder": file_path.parent.name,
                    "variable_name": name,
                    "role": "coordinate" if name in ds.coords else "data",
                    "dimensions": json_text(list(var.dims)),
                    "shape": json_text(list(var.shape)),
                    "dtype": str(var.dtype),
                    "attributes": json_text(dict(var.attrs))
                })

            if reference_schema is None:
                reference_schema = schema
            elif schema != reference_schema:
                schema_differences.append(file_path.parent.name)

    except Exception as error:
        audit_errors.append({
            "file": str(file_path),
            "error": str(error)
        })

# Save reports
with open(BASE_DIR / "file_summary.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys()) if summary_rows else None
    if writer:
        writer.writeheader()
        writer.writerows(summary_rows)

with open(BASE_DIR / "variable_schema.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "date_folder", "variable_name", "role",
            "dimensions", "shape", "dtype", "attributes"
        ]
    )
    writer.writeheader()
    writer.writerows(variable_rows)

report = [
    "INSAT-3D NETCDF STRUCTURAL AUDIT",
    "=" * 40,
    f"Expected calendar dates: {len(expected_dates)}",
    f"Available date folders: {len(folders)}",
    f"NetCDF files found: {len(nc_files)}",
    f"Successfully inspected files: {len(summary_rows)}",
    f"Failed files: {len(audit_errors)}",
    f"Missing dates: {missing_dates}",
    f"Unexpected dates: {unexpected_dates}",
    f"Files with schema differences: {schema_differences}",
    "",
    "ERRORS:"
]

for error in audit_errors:
    report.append(f"{error['file']}: {error['error']}")

report_text = "\n".join(report)

(BASE_DIR / "audit_summary.txt").write_text(
    report_text,
    encoding="utf-8"
)

print("\n" + report_text)
print("\nReports saved in:", BASE_DIR)
