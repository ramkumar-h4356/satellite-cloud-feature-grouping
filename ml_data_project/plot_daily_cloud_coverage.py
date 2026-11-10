
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "all_days_observation_audit.csv"

OUTPUT_DIR = BASE_DIR / "visualizations"
OUTPUT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(CSV_FILE)

df["date"] = pd.to_datetime(
    df["date"].str.extract(r"(\d{8})")[0],
    format="%Y%m%d"
)

daily = df.groupby("date")[["cloud_0", "cloud_1"]].sum()

daily["cloud_percentage"] = (
    daily["cloud_1"] /
    (daily["cloud_0"] + daily["cloud_1"])
) * 100

plt.figure(figsize=(13, 6))

plt.plot(
    daily.index,
    daily["cloud_percentage"],
    marker="o",
    linewidth=2
)

plt.title("Daily Cloud Coverage Over India")
plt.xlabel("Date")
plt.ylabel("Cloud Coverage (%)")
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)

plt.tight_layout()

output_file = OUTPUT_DIR / "daily_cloud_coverage.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

print(f"Graph saved successfully: {output_file}")

plt.show()
