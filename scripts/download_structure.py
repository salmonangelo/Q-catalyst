"""Download reference PDB structure (IsPETase 5XJH) from RCSB PDB."""

import argparse
from pathlib import Path
import urllib.request
import sys


def download_pdb(
    pdb_id: str = "5XJH",
    output_dir: Path | str = "data/structures",
    force: bool = False
) -> Path:
    """Download PDB file from RCSB PDB into target directory.

    Args:
        pdb_id: 4-character PDB code (e.g. 5XJH).
        output_dir: Destination directory.
        force: Overwrite if already exists.

    Returns:
        Path to downloaded PDB file.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{pdb_id.lower()}.pdb"

    if out_file.exists() and not force:
        print(f"PDB file already exists at: {out_file}")
        return out_file

    url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"
    print(f"Downloading {pdb_id.upper()} from {url}...")

    try:
        urllib.request.urlretrieve(url, out_file)
        print(f"Successfully downloaded {pdb_id.upper()} to {out_file} ({out_file.stat().st_size} bytes)")
        return out_file
    except Exception as e:
        print(f"Failed to download PDB {pdb_id}: {e}")
        if out_file.exists():
            out_file.unlink()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download PDB reference structures.")
    parser.add_argument("--pdb-id", default="5XJH", help="PDB identifier (default: 5XJH)")
    parser.add_argument("--output-dir", default="data/structures", help="Output directory")
    parser.add_argument("--force", action="store_true", help="Force overwrite")
    args = parser.parse_args()

    try:
        download_pdb(args.pdb_id, args.output_dir, args.force)
    except Exception as e:
        sys.exit(1)
