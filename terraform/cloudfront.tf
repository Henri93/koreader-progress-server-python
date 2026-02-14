# CloudFront distribution for api.null-space.xyz
# Proxies requests to the Lambda function URL

locals {
  # Extract just the domain from the function URL (strip https:// and trailing /)
  lambda_domain = trimsuffix(trimprefix(aws_lambda_function_url.api.function_url, "https://"), "/")
}

resource "aws_cloudfront_distribution" "api" {
  count = var.enable_custom_domain ? 1 : 0

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Reader Progress API - ${var.environment}"
  default_root_object = ""
  price_class         = "PriceClass_100"

  aliases = [var.api_domain_name]

  origin {
    domain_name = local.lambda_domain
    origin_id   = "lambda-function-url"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "lambda-function-url"

    forwarded_values {
      query_string = true
      headers      = ["x-auth-user", "x-auth-key", "Content-Type", "Accept", "Origin"]

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    compress               = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = var.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name        = "${var.project_name}-cloudfront"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Output the CloudFront domain for DNS setup
output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name for DNS CNAME"
  value       = var.enable_custom_domain ? aws_cloudfront_distribution.api[0].domain_name : null
}

output "cloudfront_hosted_zone_id" {
  description = "CloudFront distribution hosted zone ID for Route53 alias"
  value       = var.enable_custom_domain ? aws_cloudfront_distribution.api[0].hosted_zone_id : null
}

output "lambda_function_url" {
  description = "Direct Lambda function URL"
  value       = aws_lambda_function_url.api.function_url
}
