# Users table - PK: username (unique identifier)
resource "aws_dynamodb_table" "users" {
  name         = "${var.project_name}-${var.environment}-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "username"

  attribute {
    name = "username"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-users"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Progress table - Composite key: PK=user_id, SK=document
resource "aws_dynamodb_table" "progress" {
  name         = "${var.project_name}-${var.environment}-progress"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "document"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "document"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-progress"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Document links table - Composite key: PK=user_id, SK=document_hash
resource "aws_dynamodb_table" "document_links" {
  name         = "${var.project_name}-${var.environment}-document-links"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "document_hash"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "document_hash"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-document-links"
    Environment = var.environment
    Project     = var.project_name
  }
}
