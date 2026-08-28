"""
Upload the generated synthetic parquet files into the Unity Catalog Volume
that Lakeflow ingests from. Run after `00_setup_unity_catalog.sql` has created
the volume. Uses the Databricks SDK (picks up your CLI profile / env auth).

    python data/upload_to_volume.py
"""
from pathlib import Path
from databricks.sdk import WorkspaceClient

VOL = "/Volumes/plenitude_febar/raw/landing"
OUT = Path(__file__).resolve().parent / "output"
w = WorkspaceClient()

for f in ["customers", "consumption", "contracts", "calls", "churn_labels"]:
    src = OUT / f"{f}.parquet"
    with src.open("rb") as fh:
        w.files.upload(f"{VOL}/{f}.parquet", fh, overwrite=True)
    print(f"uploaded {src.name} -> {VOL}/{f}.parquet")
print("done — now run the Lakeflow pipeline (plenitude-febar-ingest).")
