#!/usr/bin/env python3
"""
CLI importer for chiller data from files or clipboard.
Usage:
    python import_from_file.py --file data.csv --ambient 105 --ewt 12 --lwt 7
    python import_from_file.py --clipboard --ambient 105
"""

import argparse
import sys
import os
import pyperclip
from typing import Optional
import db
import importer

def main():
    """Main CLI function."""
    
    parser = argparse.ArgumentParser(
        description="Import chiller data from file or clipboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import from CSV file with batch assignments
  python import_from_file.py --file chillers.csv --ambient 105 --ewt 12 --lwt 7
  
  # Import from TSV file
  python import_from_file.py --file data.tsv --ambient 95
  
  # Import from clipboard
  python import_from_file.py --clipboard --ambient 105 --ewt 12 --lwt 7
  
  # Import without batch assignments (will prompt for missing required fields)
  python import_from_file.py --file data.csv
        """
    )
    
    # Input source (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--file', '-f',
        type=str,
        help='Path to CSV/TSV file to import'
    )
    input_group.add_argument(
        '--clipboard', '-c',
        action='store_true',
        help='Import from clipboard (paste table data)'
    )
    
    # Batch assignment options
    parser.add_argument(
        '--ambient',
        type=int,
        choices=[95, 105, 115],
        help='Set ambient temperature for all rows (95, 105, or 115)'
    )
    parser.add_argument(
        '--ewt',
        type=float,
        help='Set entering water temperature (°C) for all rows'
    )
    parser.add_argument(
        '--lwt',
        type=float,
        help='Set leaving water temperature (°C) for all rows'
    )
    
    # Options
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview parsed data without importing'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )
    
    args = parser.parse_args()
    
    # Initialize database
    try:
        db.init_database()
        if args.verbose:
            print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)
    
    # Get data source
    if args.file:
        if not os.path.exists(args.file):
            print(f"✗ File not found: {args.file}")
            sys.exit(1)
        
        if args.verbose:
            print(f"📁 Reading file: {args.file}")
        
        try:
            imported_count, errors = importer.import_from_file(
                args.file,
                ambient_f=args.ambient,
                ewt_c=args.ewt,
                lwt_c=args.lwt
            )
        except Exception as e:
            print(f"✗ Error reading file: {e}")
            sys.exit(1)
    
    elif args.clipboard:
        if args.verbose:
            print("📋 Reading from clipboard")
        
        try:
            clipboard_data = pyperclip.paste()
            if not clipboard_data.strip():
                print("✗ No data found in clipboard")
                sys.exit(1)
            
            # Parse clipboard data
            df, parse_errors = importer.parse_table_text(
                clipboard_data,
                ambient_f=args.ambient,
                ewt_c=args.ewt,
                lwt_c=args.lwt
            )
            
            if parse_errors:
                print("⚠️  Parse warnings:")
                for error in parse_errors:
                    print(f"   - {error}")
            
            if df.empty:
                print("✗ No valid data could be parsed from clipboard")
                sys.exit(1)
            
            if args.preview:
                print("\n📊 Preview of parsed data:")
                print(df.to_string(index=False))
                return
            
            # Import to database
            imported_count, import_errors = importer.import_chillers_from_dataframe(df, db)
            errors = parse_errors + import_errors
            
        except Exception as e:
            print(f"✗ Error processing clipboard data: {e}")
            sys.exit(1)
    
    # Handle results
    if errors:
        print("⚠️  Warnings/Errors:")
        for error in errors:
            print(f"   - {error}")
        print()
    
    if imported_count > 0:
        print(f"✓ Successfully imported {imported_count} chiller records")
        
        # Show database stats
        stats = db.get_database_stats()
        print(f"📊 Database now contains {stats['total_chillers']} total chillers")
        
        if args.verbose:
            available_ambients = db.get_available_ambients()
            if available_ambients:
                print(f"🌡️  Available ambient temperatures: {', '.join(map(str, available_ambients))}°F")
    else:
        print("✗ No records were imported")
        if errors:
            print("   Check the errors above and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()
