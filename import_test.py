#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple test to check if modules can be imported.
"""

import os
import sys
import traceback

# Print current working directory
print(f"Current working directory: {os.getcwd()}")

# Print Python version
print(f"Python version: {sys.version}")
print(f"sys.path: {sys.path}")

try:
    print("Attempting to import OpenInsiderScraper...")
    import src.data.insider_data
    print("Module imported. Content:", dir(src.data.insider_data))
    
    print("All imports successful!")
except Exception as e:
    print(f"Error importing modules: {e}")
    print(f"Error type: {type(e)}")
    traceback.print_exc()
    
    # Check if the files exist
    print("\nChecking if files exist:")
    files_to_check = [
        'src/data/insider_data.py',
        'src/data/congress_data.py',
        'src/data/news_data.py'
    ]
    
    for file_path in files_to_check:
        full_path = os.path.join(os.getcwd(), file_path)
        exists = os.path.exists(full_path)
        print(f"{file_path}: {'Exists' if exists else 'Does NOT exist'}")
        
        if exists:
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    print(f"First few lines of {file_path}:")
                    for i, line in enumerate(f.readlines()[:5]):
                        print(f"  {i+1}: {line.strip()}")
            except Exception as read_e:
                print(f"Error reading file: {read_e}")
