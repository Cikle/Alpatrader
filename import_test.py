#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple test to check if all modules can be imported correctly.
This verifies that the project structure is set up correctly.
"""

import os
import sys
import traceback

# Print current working directory
print(f"Current working directory: {os.getcwd()}")

# Print Python version
print(f"Python version: {sys.version}")

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Print updated sys.path
print(f"Updated sys.path: {sys.path}")

# Track successful and failed imports
successful_imports = []
failed_imports = []

def try_import(module_name):
    """Try to import a module and report success/failure."""
    try:
        print(f"Importing {module_name}...")
        __import__(module_name)
        successful_imports.append(module_name)
        print(f"✓ Successfully imported {module_name}")
        return True
    except Exception as e:
        failed_imports.append((module_name, str(e)))
        print(f"✗ Failed to import {module_name}: {e}")
        return False

# Try to import all modules
modules_to_check = [
    'src.data.insider_data',
    'src.data.congress_data',
    'src.data.news_data',
    'src.models.signal_processor',
    'src.strategies.inverse_strategy',
    'src.utils.alpaca_wrapper',
    'src.utils.db_manager',
    'src.backtests.backtest_examples'
]

# First check the top-level package
print("\n=== Testing base imports ===")
try_import('src')

# Then check each module
print("\n=== Testing module imports ===")
for module in modules_to_check:
    try_import(module)

# Check if the files exist
print("\n=== Checking if files exist ===")
files_to_check = [
    'src/data/insider_data.py',
    'src/data/congress_data.py',
    'src/data/news_data.py',
    'src/models/signal_processor.py',
    'src/strategies/inverse_strategy.py',
    'src/utils/alpaca_wrapper.py',
    'src/utils/db_manager.py'
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
