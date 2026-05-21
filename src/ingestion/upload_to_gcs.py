"""Upload local RetailIQ sample files to Google Cloud Storage."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

from google.cloud import storage

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.utils.config import get_config


logger = logging.getLogger(__name__)

EXPECTED_FILES = ("sales.csv", "stores.csv", "features.csv", "inventory.csv", "weather.csv")


def upload_file(bucket: storage.Bucket, source_path: Path, destination_blob: str) -> None:
    """Upload one file to a GCS bucket."""
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(source_path)
    logger.info("Uploaded %s to gs://%s/%s", source_path, bucket.name, destination_blob)


def upload_sample_files(sample_dir: Path, prefix: str = "retailiq/raw") -> None:
    """Upload expected Phase 1 sample CSV files to GCS."""
    config = get_config()
    if not config.gcp_bucket_name:
        raise ValueError("GCP_BUCKET_NAME is required to upload files to GCS.")

    client = storage.Client(project=config.gcp_project_id)
    bucket = client.bucket(config.gcp_bucket_name)

    for file_name in EXPECTED_FILES:
        source_path = sample_dir / file_name
        if not source_path.exists():
            raise FileNotFoundError(f"Missing expected sample file: {source_path}")

        destination = f"{prefix}/{source_path.stem}/{source_path.name}"
        upload_file(bucket, source_path, destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload RetailIQ sample CSV files to GCS.")
    parser.add_argument("--sample-dir", type=Path, default=Path("data/sample"))
    parser.add_argument("--prefix", default="retailiq/raw")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    args = parse_args()
    upload_sample_files(args.sample_dir, args.prefix)


if __name__ == "__main__":
    main()
