import subprocess
import sys
from datetime import datetime


SCRIPTS = [
    "update_all_etfs.py",
    "update_compare_assets.py",
    "rebuild_all_rebalances.py",
]


def run_script(script_name):
    print("\n" + "=" * 70)
    print(f"Running: {script_name}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, script_name],
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"{script_name} failed with exit code {result.returncode}")

    print(f"Completed: {script_name}")


def main():
    print("MM ETFs daily update started")
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    for script in SCRIPTS:
        run_script(script)

    print("\n" + "=" * 70)
    print("MM ETFs daily update completed successfully")
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)


if __name__ == "__main__":
    main()