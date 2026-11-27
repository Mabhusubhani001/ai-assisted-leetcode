variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name (e.g., staging, production)"
  type        = string
  default     = "production"
}

# ----------------------------------------------------
# Network Topologies & CIDR Ranges
# ----------------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block for the Virtual Private Cloud"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (ALB & NAT Gateway across 2 AZs)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private app subnets (EC2 instances across 2 AZs)"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

variable "db_subnet_cidrs" {
  description = "CIDR blocks for isolated database subnets (RDS PostgreSQL across 2 AZs)"
  type        = list(string)
  default     = ["10.0.30.0/24", "10.0.40.0/24"]
}

# ----------------------------------------------------
# Compute & Auto Scaling Group Configuration
# ----------------------------------------------------
variable "instance_type" {
  description = "EC2 instance size for the Auto Scaling Group"
  type        = string
  default     = "t3.small"
}

variable "asg_min_size" {
  description = "Minimum number of EC2 instances in the Auto Scaling Group"
  type        = number
  default     = 1
}

variable "asg_max_size" {
  description = "Maximum number of EC2 instances during peak student load"
  type        = number
  default     = 4
}

variable "asg_desired_capacity" {
  description = "Baseline desired active EC2 instances"
  type        = number
  default     = 2
}

# ----------------------------------------------------
# RDS PostgreSQL Configuration
# ----------------------------------------------------
variable "db_name" {
  description = "PostgreSQL initial database name"
  type        = string
  default     = "leetcode_db"
}

variable "db_username" {
  description = "PostgreSQL administrator username"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "PostgreSQL master password (set via terraform.tfvars or TF_VAR_db_password)"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS database instance tier"
  type        = string
  default     = "db.t4g.micro"
}

# ----------------------------------------------------
# Dedicated Judge0 Sandboxed Execution Instance Toggle
# ----------------------------------------------------
variable "enable_judge0" {
  description = "Whether to provision a dedicated isolated EC2 instance for Judge0"
  type        = bool
  default     = false
}

variable "judge0_instance_type" {
  description = "EC2 instance size for dedicated Judge0 sandbox"
  type        = string
  default     = "t3.small"
}
