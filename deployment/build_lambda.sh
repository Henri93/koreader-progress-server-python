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

# Step 1: Create deployment package
echo -e "${BLUE}📦 Creating deployment package...${NC}"

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements-aws.txt --platform manylinux2014_aarch64 --target $BUILD_DIR/ --implementation cp --python-version 3.12 --only-binary=:all: --upgrade --no-cache-dir


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
zip -r "$OUTPUT_FILE" . -q

echo -e "${GREEN}✅ Package created: lambda_function.zip${NC}"

# Cleanup
rm -rf "$BUILD_DIR"

echo ""
echo "Lambda package created: $OUTPUT_FILE"
echo "Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
