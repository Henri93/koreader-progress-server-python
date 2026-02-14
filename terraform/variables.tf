variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix for resources"
  type        = string
  default     = "reader-progress"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "password_salt" {
  description = "Salt for password hashing"
  type        = string
  sensitive   = true
}

variable "enable_custom_domain" {
  description = "Enable custom domain with CloudFront"
  type        = bool
  default     = false
}

variable "api_domain_name" {
  description = "Custom domain name for the API (e.g., api.null-space.xyz)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for the custom domain"
  type        = string
  default     = ""
}
