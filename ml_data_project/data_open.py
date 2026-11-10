

import xarray as xr
import numpy as np
import pandas as pd
file_path = r"D:\Project Simulator\Satellite_Cloud_Feature_Grouping_for_Exploratory_Weather_Pattern_Analysis\ml_data_project\nices_cm4_20261001\INS3S_L3_CF_4km_Ver02_01OCT2026.nc"


ds = xr.open_dataset(file_path)

print("\nDATASET INFORMATION")
print(ds)

print("\nVARIABLES")
for variable in ds.data_vars:
    print(variable, ds[variable].shape, ds[variable].dtype)

print("\nCOORDINATES")
for coordinate in ds.coords:
    print(coordinate, ds[coordinate].shape)

print("\nLATITUDE")
print(ds["latitude"].values[:10])

print("\nLONGITUDE")
print(ds["longitude"].values[:10])

print("\nCLOUD MASK VALUES")

cloud_variable = "cloud_mask_0600"

cloud_data = ds[cloud_variable].values

unique_values, counts = np.unique(
    cloud_data,
    return_counts=True
)

for value, count in zip(unique_values, counts):
    print(f"Value: {value}, Count: {count}")

print("\nMISSING VALUES")
print(np.isnan(cloud_data).sum())

ds.close()