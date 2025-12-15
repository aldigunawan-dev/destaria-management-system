#!/bin/bash
# Quick test script - jalankan setelah setup_node.sh selesai
# Usage: bash test_node.sh

cd "$(dirname "$0")" || exit 1

echo "=================================================="
echo "Destaria Backup System - Node Test"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found. Run setup_node.sh first."
    exit 1
fi

# Check if dependencies installed
python3 -c "import requests" 2>/dev/null || {
    echo "[ERROR] Dependencies not installed. Run setup_node.sh first."
    exit 1
}

echo "[INFO] Environment ready. Running tests..."
echo ""

# Test options
echo "Available tests:"
echo "  1. Simple workflow (stop -> backup -> start -> delete)"
echo "  2. Upload existing backup to Google Drive"
echo "  3. Full workflow (all steps including upload)"
echo "  4. Check existing backups"
echo ""

read -p "Select test (1-4): " test_choice

case $test_choice in
    1)
        echo "Running: Simple Backup Workflow"
        python3 examples/test_backup_workflow_simple.py
        ;;
    2)
        echo "Running: Upload Existing Backup"
        python3 examples/test_upload_existing_backup.py
        ;;
    3)
        echo "Running: Full Workflow (with upload)"
        python3 examples/test_full_workflow.py
        ;;
    4)
        echo "Running: Check Backups"
        python3 check_backups.py
        ;;
    *)
        echo "[ERROR] Invalid choice"
        exit 1
        ;;
esac
