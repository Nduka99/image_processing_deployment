output "ecr_repository_url" {
  description = "ECR Repository URL for Docker pushes"
  value       = aws_ecr_repository.ml_inference_repo.repository_url
}

output "s3_website_url" {
  description = "Frontend S3 Static Website URL"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

output "api_gateway_url" {
  description = "API Gateway endpoint URL for /predict and /health"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.inference.function_name
}
