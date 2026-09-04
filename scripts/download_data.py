"""Download and extract the public Olist dataset without storing it in Git."""

from pathlib import Path
import shutil
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw"
ARCHIVE = ROOT / "data" / "brazilian-ecommerce.zip"
URL = "https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce"


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(URL, timeout=180) as response, ARCHIVE.open("wb") as output:
        shutil.copyfileobj(response, output)
    with zipfile.ZipFile(ARCHIVE) as archive:
        for member in archive.infolist():
            destination = (DATA / member.filename).resolve()
            if DATA.resolve() not in destination.parents and destination != DATA.resolve():
                raise ValueError(f"Unsafe archive path: {member.filename}")
        archive.extractall(DATA)
    ARCHIVE.unlink()
    print(f"Dataset extracted to {DATA}")


if __name__ == "__main__":
    main()
