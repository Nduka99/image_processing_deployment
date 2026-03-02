terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure the AWS Provider
# The region is handled dynamically via the AWS CLI profile we configured
provider "aws" {
  region = "eu-west-2"
}

# 1. Elastic Container Registry (ECR)
# This is where our Docker image will be pushed and stored.
resource "aws_ecr_repository" "ml_inference_repo" {
  name                 = "image-processing-inference"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Future Additions (Phase 5):
# Add AWS App Runner or AWS ECS Fargate configuration here.
# Targeting minimal provision limits (e.g., 0.25 vCPU, 0.5 GB memory)
# to stay safely inside the AWS Free Tier limitations.
