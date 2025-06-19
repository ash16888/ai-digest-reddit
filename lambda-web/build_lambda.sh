#!/bin/bash

# Build script for AWS Lambda deployment package
set -e

echo "Building Lambda deployment package..."

# Save project root directory
PROJECT_ROOT=$(pwd)

# Clean up any existing deployment files
rm -f lambda_deployment.zip

# Create temporary directory for building
BUILD_DIR=$(mktemp -d)
echo "Using build directory: $BUILD_DIR"

# Copy source code
echo "Copying source code..."
cp -r src/ "$BUILD_DIR/"
cp lambda_handler.py "$BUILD_DIR/"
cp requirements.txt "$BUILD_DIR/"

# Install dependencies
echo "Installing Python dependencies..."
cd "$BUILD_DIR"
pip install -r requirements.txt -t . --no-cache-dir

# Remove unnecessary files to reduce package size
echo "Cleaning up unnecessary files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
rm -rf .pytest_cache 2>/dev/null || true

# Remove large unused packages if they exist
rm -rf boto3/ botocore/ 2>/dev/null || true  # AWS Lambda provides these

# Create deployment package
echo "Creating deployment package..."
zip -r lambda_deployment.zip . -x "*.git*" "*.DS_Store*" 

# Move to project root
echo "Moving zip to project root: $PROJECT_ROOT"
cp lambda_deployment.zip "$PROJECT_ROOT/"

# Return to original directory
cd "$PROJECT_ROOT"

# Verify file was created
if [ -f "lambda_deployment.zip" ]; then
    echo "✅ Lambda deployment package created successfully!"
else
    echo "❌ Failed to create deployment package"
    exit 1
fi

# Clean up
rm -rf "$BUILD_DIR"

echo "Lambda deployment package created: lambda_deployment.zip"
echo "Package size: $(du -h lambda_deployment.zip | cut -f1)"