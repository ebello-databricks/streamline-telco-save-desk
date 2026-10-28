# Deploy runbook (optional live workspace run)

The submission stands on the committed text evidence. To run it live in a workspace (e.g. a FEVM or e2-demo-field-eng):

```bash
databricks auth login --profile e2-demo
python data/generate_synthetic_data.py

# 1. Catalog, schemas, landing volume (first block of 00_setup_unity_catalog.sql)
# 2. Upload landing files (one folder per entity, for Auto Loader)
for f in subscribers contracts usage care_calls churn_labels; do
  databricks fs cp data/output/$f.parquet dbfs:/Volumes/streamline_telco/raw/landing/$f/$f.parquet --overwrite -p e2-demo
done

# 3. Deploy and run the whole journey
databricks bundle deploy -t dev -p e2-demo --var warehouse_id=<serverless-warehouse-id>
databricks bundle run save_desk_nightly -t dev -p e2-demo
```

4. Genie: New → Genie space; add the three tables from `genie/genie_space_config.json`; paste the instructions, sample questions and trusted SQL; put the space id in the config and run `notebooks/05_genie_agent.py`.
5. App: `databricks bundle run save_desk -t dev`. The app reads Lakebase through the `lakebase` resource.

Teardown: `databricks bundle destroy -t dev -p e2-demo`, then `DROP CATALOG streamline_telco CASCADE`.
