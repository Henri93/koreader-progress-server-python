#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$SCRIPT_DIR/build"
OUTPUT_FILE="$SCRIPT_DIR/lambda_package.zip"

echo "Building Lambda package..."

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r "$PROJECT_ROOT/requirements-aws.txt" -t package/ --quiet

# Copy application code
echo "Copying application code..."
cp "$PROJECT_ROOT/main.py" "$BUILD_DIR/"
cp "$PROJECT_ROOT/auth.py" "$BUILD_DIR/"
cp "$PROJECT_ROOT/schemas.py" "$BUILD_DIR/"
cp "$PROJECT_ROOT/lambda_handler.py" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/repositories" "$BUILD_DIR/"

# Create zip
echo "Creating zip archive..."
cd "$BUILD_DIR"
rm -f "$OUTPUT_FILE"
zip -r "$OUTPUT_FILE" . -x "*.pyc" -x "__pycache__/*" -x "*.dist-info/*" -x "*.egg-info/*"

# Cleanup
rm -rf "$BUILD_DIR"

echo ""
echo "Lambda package created: $OUTPUT_FILE"
echo "Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
