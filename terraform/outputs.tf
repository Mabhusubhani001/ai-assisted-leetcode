# ----------------------------------------------------
# Application URL & Load Balancer Endpoint
# ----------------------------------------------------
output "application_url" {
  description = "Public HTTP URL of the DSA Assessment Platform via Application Load Balancer"
  value       = "http://${aws_lb.main.dns_name}"
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

# ----------------------------------------------------
# Production Database Connection Endpoint
# ----------------------------------------------------
output "rds_endpoint" {
  description = "Private connection endpoint for PostgreSQL RDS"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_database_name" {
  description = "Database name inside PostgreSQL"
  value       = aws_db_instance.postgres.db_name
}

# ----------------------------------------------------
# Dedicated Judge0 Private IP (If Enabled)
# ----------------------------------------------------
output "judge0_private_ip" {
  description = "Private IP address of the dedicated Judge0 sandbox instance"
  value       = var.enable_judge0 ? aws_instance.judge0[0].private_ip : "Disabled (Using internal execution runner)"
}
