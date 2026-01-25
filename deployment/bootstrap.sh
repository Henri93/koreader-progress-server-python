#!/bin/bash
set -e

BUCKET_NAME="nullspace-terraform-state"
REGION="us-east-1"

echo "=== Terraform State Bucket Bootstrap ==="
echo ""
echo "This script creates the S3 bucket for Terraform remote state."
echo "Run this once before deploying reader-progress or nullspace-website."
echo ""

# Check if bucket already exists
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "Bucket '$BUCKET_NAME' already exists."
    exit 0
fi

echo "Creating S3 bucket: $BUCKET_NAME"
aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --region "$REGION"

echo "Enabling versioning..."
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled

echo "Enabling encryption..."
aws s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }'

echo "Blocking public access..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration '{
        "BlockPublicAcls": true,
        "IgnorePublicAcls": true,
        "BlockPublicPolicy": true,
        "RestrictPublicBuckets": true
    }'

echo ""
echo "=== Bootstrap Complete ==="
echo "S3 bucket '$BUCKET_NAME' is ready for Terraform state storage."
