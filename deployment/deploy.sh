#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"
FUNCTION_NAME="reader-progress-prod"
REGION="us-east-1"

echo "=== Reader Progress AWS Deployment ==="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    echo "Error: Terraform is not installed"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS credentials not configured"
    exit 1
fi

echo "All prerequisites met."
echo ""

# Build Lambda package
echo "Building Lambda package..."
bash "$SCRIPT_DIR/build_lambda.sh"
echo ""

# Initialize Terraform
echo "Initializing Terraform..."
cd "$TERRAFORM_DIR"
terraform init

echo ""
echo "Planning deployment..."
terraform plan

echo ""
read -p "Do you want to apply these changes? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "Applying changes..."
terraform apply -auto-approve

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Lambda function deployed. Now update nullspace-website to add API Gateway routes."
echo ""
echo "Outputs:"
terraform output

# echo -e "${BLUE}🔄 Updating Lambda function...${NC}"
# aws lambda update-function-code \
#     --function-name "$FUNCTION_NAME" \
#     --zip-file fileb://lambda_package.zip \
#     --region "$REGION" \
#     --no-cli-pager

# echo -e "${GREEN}✅ Lambda function updated successfully!${NC}"
