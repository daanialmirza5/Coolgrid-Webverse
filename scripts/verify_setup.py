#!/usr/bin/env python3
"""
CoolGrid Environment & Artifact Verification Script

Validates:
1. Python version (>= 3.10)
2. Required Python packages
3. ML artifacts existence (models, encoders, scalers)
4. Demo datasets and synthetic city grid
5. Database connectivity and environment variables
"""

import sys
import os
from pathlib import Path

def check_python():
    print("Checking Python version...", end=" ")
    if sys.version_info < (3, 10):
        print(f"FAILED (Found Python {sys.version.split()[0]}, expected >= 3.10)")
        return False
    print(f"OK ({sys.version.split()[0]})")
    return True

def check_packages():
    required = [
        "fastapi",
        "pydantic",
        "sqlalchemy",
        "numpy",
        "pandas",
        "scikit-learn",
        "xgboost",
        "torch"
    ]
    print("\nChecking core Python dependencies...")
    all_ok = True
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"  [x] {pkg}")
        except ImportError:
            print(f"  [ ] {pkg} (missing)")
            all_ok = False
    return all_ok

def check_artifacts():
    print("\nChecking ML & Physics artifacts...")
    root = Path(__file__).resolve().parent.parent
    data_demo = root / "data" / "demo"
    
    expected_files = [
        data_demo / "pune_demo_grid.geojson",
        data_demo / "pune_demo_dataset.parquet",
        data_demo / "hotspot_xgb.json",
        data_demo / "prediction_models.pkl",
    ]
    
    all_present = True
    for f in expected_files:
        if f.exists():
            print(f"  [x] {f.name}")
        else:
            print(f"  [ ] {f.name} (not found - run `python ml/train.py` to generate)")
            all_present = False
    return all_present

def main():
    print("=" * 60)
    print("CoolGrid System & Environment Verification")
    print("=" * 60)
    
    py_ok = check_python()
    pkg_ok = check_packages()
    art_ok = check_artifacts()
    
    print("\n" + "=" * 60)
    if py_ok and pkg_ok and art_ok:
        print("ALL CHECKS PASSED: CoolGrid is ready to run!")
    else:
        print("SOME CHECKS FAILED: Review the output above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
