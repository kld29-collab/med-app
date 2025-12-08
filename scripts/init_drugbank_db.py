#!/usr/bin/env python
"""
DrugBank Database Initialization Script

This script creates the SQLite database from the full_database.xml file.
Run this once to initialize the database, then it will be reused.

Usage:
    python scripts/init_drugbank_db.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.drugbank_db import DrugBankDatabase


def main():
    """Initialize DrugBank database."""
    base_path = Path(__file__).parent.parent
    db_file = base_path / "data" / "drugbank.db"
    xml_file = base_path / "data" / "full_database.xml"
    
    print(f"DrugBank Database Initialization")
    print(f"=" * 50)
    print(f"XML file: {xml_file}")
    print(f"Database file: {db_file}")
    print()
    
    # Check if files exist
    if not xml_file.exists():
        print(f"ERROR: XML file not found at {xml_file}")
        return 1
    
    print(f"XML file size: {xml_file.stat().st_size / (1024**3):.2f} GB")
    print()
    
    # Check if database already exists
    if db_file.exists():
        response = input(f"Database already exists. Recreate? (y/n): ")
        if response.lower() != "y":
            print("Cancelled.")
            return 0
        print(f"Removing existing database...")
        db_file.unlink()
    
    print(f"Creating database from XML...")
    print(f"This may take 5-30 minutes depending on system performance.")
    print()
    
    db = DrugBankDatabase(str(db_file), str(xml_file))
    
    try:
        success = db.initialize()
        if success:
            print()
            print(f"SUCCESS: Database created successfully!")
            print(f"Database size: {db_file.stat().st_size / (1024**3):.2f} GB")
            return 0
        else:
            print()
            print(f"ERROR: Failed to create database")
            return 1
    except KeyboardInterrupt:
        print()
        print(f"Interrupted by user.")
        if db_file.exists():
            print(f"Cleaning up incomplete database...")
            db_file.unlink()
        return 1
    except Exception as e:
        print()
        print(f"ERROR: {str(e)}")
        if db_file.exists():
            print(f"Cleaning up incomplete database...")
            db_file.unlink()
        return 1


if __name__ == "__main__":
    sys.exit(main())
