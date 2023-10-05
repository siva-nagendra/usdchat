#!/bin/bash

# Run Black
echo "Running Black..."
black --check . || black .
echo "Black completed."

# Run Pylint
echo "Running Pylint..."
find . -name "*.py" | xargs pylint || (echo "Pylint found issues, attempting to auto-fix..." && autopep8 --in-place --aggressive --aggressive *.py && pylint *.py)
echo "Pylint completed."

# Run tests
echo "Running tests..."
python -m unittest discover -s . -p "*_test.py"
echo "Testing completed."
pylint *.py || (echo "Pylint found issues, attempting to auto-fix..." && autopep8 --in-place --aggressive --aggressive torrento.py && pylint *.py)
echo "Pylint completed."

echo "Testing completed."