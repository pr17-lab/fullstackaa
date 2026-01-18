"""
Data Migrations Module

This directory contains data migrations with version control and rollback capability.

Structure:
- base.py - Abstract base class for all data migrations
- m_XXX_*.py - Individual migration files (numbered sequentially with m_ prefix)

Usage:
    python scripts/run_data_migration.py --version 002 --direction upgrade
    python scripts/run_data_migration.py --version 002 --direction downgrade
"""
