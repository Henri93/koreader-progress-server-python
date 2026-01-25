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

# Check if Docker is available for cross-platform build
if command -v docker &> /dev/null; then
    echo "Using Docker for cross-platform build (Amazon Linux 2023)..."

    # Install dependencies using Lambda Python image
    docker run --rm \
        --entrypoint "" \
        -v "$PROJECT_ROOT:/var/task" \
        -v "$BUILD_DIR:/var/build" \
        public.ecr.aws/lambda/python:3.12 \
        pip install -r /var/task/requirements-aws.txt -t /var/build --quiet --upgrade
else
    echo "Docker not found, using local pip (may not work on Lambda)..."
    pip3 install -r "$PROJECT_ROOT/requirements-aws.txt" -t "$BUILD_DIR" --quiet --upgrade
fi

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
