
from pathlib import Path
import xarray as xr

BASE_DIR = Path(__file__).resolve().parent
files = sorted(BASE_DIR.glob("nices_cm4_*/*.nc"))

if not files:
    raise RuntimeError("No NetCDF files found.")

def inspect_schema(path):
    with xr.open_dataset(
        path,
        engine="netcdf4",
        decode_cf=False,
        mask_and_scale=False
    ) as ds:
        dimensions = dict(ds.sizes)

        variables = {
            name: {
                "dims": tuple(var.dims),
                "dtype": str(var.dtype)
            }
            for name, var in ds.variables.items()
        }

        return dimensions, variables

reference_path = files[0]
ref_dimensions, ref_variables = inspect_schema(reference_path)

print("REFERENCE:", reference_path.parent.name)
print("Dimensions:", ref_dimensions)
print("Variables:", len(ref_variables))

for path in files[1:]:
    dimensions, variables = inspect_schema(path)
    differences = []

    if dimensions != ref_dimensions:
        differences.append(
            f"Dimension sizes: {dimensions}"
        )

    missing = set(ref_variables) - set(variables)
    extra = set(variables) - set(ref_variables)

    if missing:
        differences.append(f"Missing variables: {sorted(missing)}")

    if extra:
        differences.append(f"Additional variables: {sorted(extra)}")

    for name in set(ref_variables) & set(variables):
        ref = ref_variables[name]
        current = variables[name]

        if ref["dims"] != current["dims"]:
            differences.append(
                f"{name}: dimensions {ref['dims']} -> {current['dims']}"
            )

        if ref["dtype"] != current["dtype"]:
            differences.append(
                f"{name}: dtype {ref['dtype']} -> {current['dtype']}"
            )

    if differences:
        print(f"\n{path.parent.name}")
        for difference in differences:
            print("  -", difference)

print("\nSchema comparison completed.")

