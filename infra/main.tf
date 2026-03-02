terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-west-2"
}

locals {
  project_name = "cat-vs-dog"
  account_id   = "235899055608"
  region       = "eu-west-2"
}

# ──────────────────────────────────────────────────────────────
# 1. ECR Repository (Docker Image Storage)
# Free Tier: 500 MB private repository storage
# ──────────────────────────────────────────────────────────────
resource "aws_ecr_repository" "ml_inference_repo" {
  name                 = "image-processing-inference"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Lifecycle policy: keep only last 2 images to stay under 500MB
resource "aws_ecr_lifecycle_policy" "cleanup" {
  repository = aws_ecr_repository.ml_inference_repo.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only last 2 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 2
      }
      action = {
        type = "expire"
      }
    }]
  })
}

# ──────────────────────────────────────────────────────────────
# 2. S3 Bucket (Frontend Static Website Hosting)
# Free Tier: 5 GB storage, 20K GET requests/month
# ──────────────────────────────────────────────────────────────
resource "aws_s3_bucket" "frontend" {
  bucket        = "${local.project_name}-frontend-${local.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "frontend_public_read" {
  bucket     = aws_s3_bucket.frontend.id
  depends_on = [aws_s3_bucket_public_access_block.frontend]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadGetObject"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.frontend.arn}/*"
    }]
  })
}

# ──────────────────────────────────────────────────────────────
# 3. IAM Role for Lambda
# ──────────────────────────────────────────────────────────────
resource "aws_iam_role" "lambda_exec" {
  name = "${local.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ──────────────────────────────────────────────────────────────
# 4. Lambda Function (ML Inference Backend)
# Free Tier: 1M requests, 400K GB-seconds/month (ALWAYS FREE)
# ──────────────────────────────────────────────────────────────
resource "aws_lambda_function" "inference" {
  function_name = "${local.project_name}-inference"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.ml_inference_repo.repository_url}:latest"
  timeout       = 60
  memory_size   = 1024  # 1 GB — needed for ML inference + feature extraction

  environment {
    variables = {
      PYTHONPATH = "/app"
    }
  }

  depends_on = [aws_ecr_repository.ml_inference_repo]

  lifecycle {
    ignore_changes = [image_uri]
  }
}

# ──────────────────────────────────────────────────────────────
# 5. API Gateway (REST API — Routes to Lambda)
# Free Tier: 1M API calls/month (12 months)
# ──────────────────────────────────────────────────────────────
resource "aws_apigatewayv2_api" "api" {
  name          = "${local.project_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "GET", "OPTIONS"]
    allow_headers = ["*"]
    max_age       = 86400
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.inference.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "predict" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "POST /predict"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.inference.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}
