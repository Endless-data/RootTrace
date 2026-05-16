# Generated Data Output

This directory is the default output location for simulated RootTrace CSV files.

Generated `.csv` and `manifest.json` files are intentionally ignored by git. Regenerate them locally with:

```bash
uv run python scripts/generate_simulated_data.py --output data/generated --seed 20260516
```
