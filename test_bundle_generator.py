#!/usr/bin/env python3
"""
Simple script to test the bundle generator functionality locally.
"""
import os
import sys
import argparse
from lib.bundle_generator import BundleGenerator
from lib.firebase_handler import FirebaseHandler

def main():
    parser = argparse.ArgumentParser(description="Test Firestore bundle generator")
    parser.add_argument(
        "--collection", 
        help="Specific collection path to generate bundle for (e.g. 'imps/username/trophies2023')"
    )
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Generate bundles for all imp trophy collections"
    )
    parser.add_argument(
        "--year", 
        type=int,
        help="Year to use for trophy collections (default: current year)",
        default=None
    )
    parser.add_argument(
        "--output", 
        help="Output directory for bundles (default: ./bundles)",
        default="bundles"
    )
    
    args = parser.parse_args()
    
    if not args.collection and not args.all:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Initialize Firebase handler with optional year
        firebase_handler = FirebaseHandler(year=args.year)
        
        # Create bundle generator
        bundle_generator = BundleGenerator(firebase_handler)
        
        # Ensure output directory exists
        os.makedirs(args.output, exist_ok=True)
        
        if args.all:
            print("Generating bundles for all imp trophy collections...")
            filepaths = bundle_generator.generate_all_bundles(args.output)
            print(f"Generated {len(filepaths)} bundle files:")
            for filepath in filepaths:
                print(f"  - {filepath}")
        else:
            print(f"Generating bundle for {args.collection}...")
            bundle_data = bundle_generator.generate_bundle(args.collection)
            filepath = bundle_generator.save_bundle(bundle_data, args.collection, args.output)
            print(f"Bundle saved to {filepath}")
            print(f"Total documents: {bundle_data['metadata']['totalDocuments']}")
            print(f"Total bytes: {bundle_data['metadata']['totalBytes']}")
            
        print("Bundle generation completed successfully")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 