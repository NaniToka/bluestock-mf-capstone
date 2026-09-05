#!/bin/bash
set -e
echo "1. generate_eda_notebook.py"
python3 scripts/generate_eda_notebook.py
echo "2. jupyter nbconvert eda_analysis"
python3 -m jupyter nbconvert --to notebook --execute notebooks/03_eda_analysis.ipynb --inplace
echo "3. compute_metrics.py"
python3 scripts/compute_metrics.py
echo "4. generate_advanced_notebook.py"
python3 scripts/generate_advanced_notebook.py
echo "5. jupyter nbconvert advanced_analytics"
python3 -m jupyter nbconvert --to notebook --execute notebooks/05_advanced_analytics.ipynb --inplace
echo "6. validate.py"
python3 dashboard/validate.py
echo "7. capture_dashboard_screenshots.py"
python3 scripts/capture_dashboard_screenshots.py
echo "8. generate_report.py"
python3 scripts/generate_report.py
echo "9. generate_presentation.py"
python3 scripts/generate_presentation.py
echo "ALL DONE SUCCESSFULLY!"
