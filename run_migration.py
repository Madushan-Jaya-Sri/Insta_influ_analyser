#!/usr/bin/env python3
"""
Script to run database migration for Instagram Influencer Analyzer
"""
import os
import sys
from migrations.update_history_model import migrate_database

if __name__ == "__main__":
    print("Starting database migration...")
    migrate_database()
    print("Migration process completed.") 