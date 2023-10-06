#!/bin/bash

# Run Black
echo "Running Black..."
black --check . || black .
echo "Black completed."

# Run Pylint and auto-fix with autopep8 if necessary
echo "Running Pylint..."
find . -name "*.py" | while read -r file; do
    pylint "$file" || (echo "Pylint found issues in $file, attempting to auto-fix..." && autopep8 --in-place --aggressive --aggressive "$file" && pylint "$file")
done
echo "Pylint completed."

# Run isort
echo "Running isort..."
isort .
echo "isort completed."

# Run tests
echo "Running tests..."
python -m unittest discover -s . -p "*_test.py"
echo "Testing completed."
