import json
from pathlib import Path

ETFS_ROOT = Path("etfs")


def load_etfs():
    etfs = []

    if not ETFS_ROOT.exists():
        return etfs

    for etf_dir in ETFS_ROOT.iterdir():
        if not etf_dir.is_dir():
            continue

        metadata_path = etf_dir / "metadata.json"

        if not metadata_path.exists():
            continue

        with open(metadata_path, "r", encoding="utf-8") as file:
            metadata = json.load(file)

        metadata["folder"] = str(etf_dir)
        metadata["portfolio_path"] = str(etf_dir / metadata["portfolio_file"])
        metadata["db_path"] = str(etf_dir / metadata["db_file"])

        etfs.append(metadata)

    return etfs