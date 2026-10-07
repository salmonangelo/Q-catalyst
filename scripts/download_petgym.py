"""PET-Gym benchmark dataset import and documentation helper."""

import argparse
from pathlib import Path
import sys
import pandas as pd


PETGYM_OVERVIEW = """
================================================================================
Q-CATALYST: PET-Gym Benchmark Import Guide
================================================================================
PET-Gym is the primary empirical benchmark for PETase variant activity, thermal
stability, and multi-site mutational epistasis across multiple PET-degrading
enzymes (including IsPETase, LCC, and homologs).

INSTRUCTIONS FOR DATA IMPORT:
1. Place raw PET-Gym CSV / Parquet files into:
   data/raw/

   Examples:
   - data/raw/petgym_single_mutants.csv
   - data/raw/petgym_multi_mutants.csv
   - data/raw/literature_variants.csv

2. Verify raw file columns contain at minimum:
   - Variant identification (e.g. 'variant', 'mutations', or 'sequence')
   - Activity / Fitness (e.g. 'rel_activity', 'fitness', 'activity')
   - Parent scaffold (e.g. 'parent', 'wild_type' - defaults to IsPETase if omitted)

3. Run data curation pipeline:
   python data/build_dataset.py

4. Validate curated dataset and generate data quality report:
   python data/validate.py data/curated/variants.parquet

5. Create leakage-aware splits:
   python -c "from data.split import DatasetSplitter; import pandas as pd; df = pd.read_parquet('data/curated/variants.parquet'); s = DatasetSplitter(); m = s.split(df, strategy='mutation_complexity'); m.save_json('data/splits/split_mutation_complexity.json')"
================================================================================
"""


def check_dataset_status(raw_dir: Path | str = "data/raw") -> bool:
    """Check whether raw benchmark datasets are present locally."""
    p = Path(raw_dir)
    if not p.exists():
        print(f"[STATUS]: Raw data directory '{p}' does not exist.")
        return False

    raw_files = [f for f in p.glob("*") if f.suffix.lower() in (".csv", ".parquet", ".tsv", ".json")]
    if not raw_files:
        print(f"[STATUS]: No raw dataset files found in '{p}'.")
        print(PETGYM_OVERVIEW)
        return False

    print(f"[STATUS]: Found {len(raw_files)} raw data files in '{p}':")
    for f in raw_files:
        print(f"  - {f.name} ({f.stat().st_size} bytes)")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PET-Gym benchmark import helper.")
    parser.add_argument("--raw-dir", default="data/raw", help="Raw data directory")
    args = parser.parse_args()

    found = check_dataset_status(args.raw_dir)
    sys.exit(0 if found else 0)
