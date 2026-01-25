# Outputs for cross-stack reference via remote state

output "lambda_arn" {
  description = "ARN of the Lambda function (used by nullspace-website for API Gateway integration)"
  value       = aws_lambda_function.api.arn
}

output "lambda_invoke_arn" {
  description = "Invoke ARN of the Lambda function (used for API Gateway integration)"
  value       = aws_lambda_function.api.invoke_arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.api.function_name
}

output "users_table_name" {
  description = "DynamoDB users table name"
  value       = aws_dynamodb_table.users.name
}

output "users_table_arn" {
  description = "DynamoDB users table ARN"
  value       = aws_dynamodb_table.users.arn
}

output "progress_table_name" {
  description = "DynamoDB progress table name"
  value       = aws_dynamodb_table.progress.name
}

output "progress_table_arn" {
  description = "DynamoDB progress table ARN"
  value       = aws_dynamodb_table.progress.arn
}
