
from pathlib import Path
import xarray as xr
import re

BASE_DIR = Path(
    r"D:\Project Simulator\Satellite_Cloud_Feature_Grouping_for_Exploratory_Weather_Pattern_Analysis\ml_data_project"
)

DATES = ["20261025", "20261026", "20261028"]


def find_netcdf(folder):
    files = list(folder.glob("*.nc"))

    if not files:
        raise FileNotFoundError(f"No NetCDF file found in {folder}")

    if len(files) > 1:
        raise ValueError(f"Multiple NetCDF files found in {folder}")

    return files[0]


def inspect_dataset(date):
    folder = BASE_DIR / f"nices_cm4_{date}"
    nc_file = find_netcdf(folder)

    print("\n" + "=" * 70)
    print(f"DATE: {date}")
    print("=" * 70)

    with xr.open_dataset(
        nc_file,
        decode_cf=False,
        mask_and_scale=False
    ) as ds:

        print("\nDimensions:")
        print(ds.sizes)

        print("\nGlobal attributes:")
        for key, value in ds.attrs.items():
            print(f"{key}: {value}")

        cloud_times = sorted(
            re.findall(r"cloud_mask_(\d{4})", " ".join(ds.data_vars))
        )

        flag_times = sorted(
            re.findall(r"flag_(\d{4})", " ".join(ds.data_vars))
        )

        print("\nAvailable cloud-mask timestamps:")
        print(cloud_times)

        print("\nAvailable flag timestamps:")
        print(flag_times)

        print("\nCloud-mask and flag variable details:")

        for name, variable in ds.data_vars.items():
            if name.startswith(("cloud_mask_", "flag_")):
                print(
                    name,
                    "| Shape:", variable.shape,
                    "| Dtype:", variable.dtype,
                    "| Attributes:", variable.attrs
                )


def compare_documentation():
    print("\n" + "=" * 70)
    print("DOCUMENTATION COMPARISON")
    print("=" * 70)

    for filename in ["cm4_meta.xml", "readme.txt", "policy.txt"]:
        print(f"\nFILE: {filename}")

        contents = {}

        for date in DATES:
            path = BASE_DIR / f"nices_cm4_{date}" / filename

            if path.exists():
                contents[date] = path.read_text(
                    encoding="utf-8",
                    errors="replace"
                )
            else:
                contents[date] = None

        reference = contents["20261025"]

        for date, content in contents.items():
            if content is None:
                print(f"{date}: File missing")
            elif content == reference:
                print(f"{date}: Identical to October 25")
            else:
                print(f"{date}: DIFFERENT from October 25")

        oct26_content = contents["20261026"]

        if oct26_content is not None:
            print("\nOctober 26 document content:")
            print(oct26_content[:10000])


for date in DATES:
    inspect_dataset(date)

compare_documentation()
