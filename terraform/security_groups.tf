# ----------------------------------------------------
# 1. Application Load Balancer (ALB) Security Group
# Accepts HTTP (80) and HTTPS (443) from the public internet.
# ----------------------------------------------------
resource "aws_security_group" "alb" {
  name        = "${var.environment}-alb-sg"
  description = "Allows incoming public student traffic to Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Public HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Public HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound to internal application targets"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-alb-sg"
  }
}

# ----------------------------------------------------
# 2. EC2 Application Instances Security Group
# Accepts traffic on 3000 (Frontend) and 8000 (FastAPI) ONLY from the ALB.
# Blocks direct internet access.
# ----------------------------------------------------
resource "aws_security_group" "app" {
  name        = "${var.environment}-ec2-app-sg"
  description = "Restricts traffic to EC2 app instances strictly from the ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Next.js Frontend from ALB"
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description     = "FastAPI Backend API from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Outbound to NAT gateway for Gemini API, Docker pulls, and database"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-ec2-app-sg"
  }
}

# ----------------------------------------------------
# 3. RDS PostgreSQL Security Group
# Accepts port 5432 strictly from the EC2 application security group.
# ----------------------------------------------------
resource "aws_security_group" "db" {
  name        = "${var.environment}-rds-postgres-sg"
  description = "Allows PostgreSQL connections strictly from backend EC2 instances"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL port 5432 from EC2 App"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    description = "No outbound needed from database"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-rds-postgres-sg"
  }
}

# ----------------------------------------------------
# 4. Dedicated Judge0 Sandboxed Execution Security Group
# Accepts submissions on port 2358 strictly from the FastAPI backend.
# Completely blocked from accessing the RDS database.
# ----------------------------------------------------
resource "aws_security_group" "judge0" {
  name        = "${var.environment}-judge0-sandbox-sg"
  description = "Isolates Judge0 execution runner: allows port 2358 strictly from FastAPI"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Judge0 API from FastAPI backend"
    from_port       = 2358
    to_port         = 2358
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    description = "Outbound for Docker package updates"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-judge0-sandbox-sg"
  }
}
