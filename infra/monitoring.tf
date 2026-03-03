# ──────────────────────────────────────────────────────────────
# Phase 6: The Watch (Autonomous Monitoring & Remediation)
# CloudWatch Alarms + SNS Alerts + Billing Protection
# All resources are FREE TIER (CloudWatch basic metrics, SNS)
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 1. SNS Topic for All Alerts
# Free Tier: 1M publishes, 100K HTTP deliveries/month
# ──────────────────────────────────────────────────────────────
resource "aws_sns_topic" "alerts" {
  name = "${local.project_name}-alerts"
}

# Email subscription — user receives alerts via email
variable "alert_email" {
  description = "Email address for monitoring alerts"
  type        = string
  default     = "nduka99@hotmail.co.uk"
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ──────────────────────────────────────────────────────────────
# 2. CloudWatch Alarm: Lambda Errors (5XX)
# Triggers if ANY invocation errors occur in 5 minutes
# ──────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.project_name}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alert: Lambda function is throwing errors!"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.inference.function_name
  }
}

# ──────────────────────────────────────────────────────────────
# 3. CloudWatch Alarm: Lambda Duration (Near Timeout)
# Triggers if average duration exceeds 50s (timeout is 60s)
# ──────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${local.project_name}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Average"
  threshold           = 50000  # 50 seconds in milliseconds
  alarm_description   = "Warning: Lambda inference approaching timeout (50s/60s)!"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.inference.function_name
  }
}

# ──────────────────────────────────────────────────────────────
# 4. CloudWatch Alarm: Lambda Throttles
# Triggers if Lambda is being throttled (Free Tier concurrency limit)
# ──────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${local.project_name}-lambda-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alert: Lambda is being throttled! Free Tier concurrency may be exceeded."
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.inference.function_name
  }
}

# ──────────────────────────────────────────────────────────────
# 5. CloudWatch Alarm: API Gateway 5XX Errors
# Monitors the HTTP API for server-side errors
# ──────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  alarm_name          = "${local.project_name}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "5xx"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert: API Gateway returning 5XX errors!"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApiId = aws_apigatewayv2_api.api.id
  }
}

# ──────────────────────────────────────────────────────────────
# 6. AWS Budget: Free Tier Cost Protection ($0.01 threshold)
# ──────────────────────────────────────────────────────────────
resource "aws_budgets_budget" "free_tier_guard" {
  name         = "${local.project_name}-free-tier-guard"
  budget_type  = "COST"
  limit_amount = "1.00"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 1
    threshold_type             = "ABSOLUTE_VALUE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }
}
