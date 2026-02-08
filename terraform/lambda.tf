# Lambda function
resource "aws_lambda_function" "api" {
  filename         = "../deployment/lambda_package.zip"
  function_name    = "${var.project_name}-${var.environment}"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_handler.handler"
  runtime          = "python3.12"
  architectures    = ["arm64"]
  timeout          = 30
  memory_size      = 256
  source_code_hash = filebase64sha256("../deployment/lambda_package.zip")

  environment {
    variables = {
      DB_BACKEND                    = "dynamodb"
      DYNAMODB_USERS_TABLE          = aws_dynamodb_table.users.name
      DYNAMODB_PROGRESS_TABLE       = aws_dynamodb_table.progress.name
      DYNAMODB_DOCUMENT_LINKS_TABLE = aws_dynamodb_table.document_links.name
      PASSWORD_SALT                 = var.password_salt
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy.lambda_dynamodb
  ]

  tags = {
    Name        = "${var.project_name}-lambda"
    Environment = var.environment
    Project     = var.project_name
  }
}
