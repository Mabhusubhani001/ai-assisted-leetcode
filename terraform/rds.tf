# ----------------------------------------------------
# RDS Subnet Group (Spans 2 Private Database Subnets)
# ----------------------------------------------------
resource "aws_db_subnet_group" "main" {
  name        = "${var.environment}-dsa-db-subnet-group"
  description = "Isolated private database subnets across 2 AZs"
  subnet_ids  = aws_subnet.db[*].id

  tags = {
    Name = "${var.environment}-dsa-db-subnet-group"
  }
}

# ----------------------------------------------------
# Production PostgreSQL RDS Instance
# ----------------------------------------------------
resource "aws_db_instance" "postgres" {
  identifier            = "${var.environment}-leetcode-postgres"
  engine                = "postgres"
  engine_version        = "16.16"
  instance_class        = var.db_instance_class
  allocated_storage     = 20
  max_allocated_storage = 100 # Auto-scales disk storage up to 100 GB
  storage_type          = "gp3"

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]

  multi_az            = false # Set to true for enterprise high-availability multi-AZ standby
  publicly_accessible = false # Zero direct internet access
  skip_final_snapshot = true  # Set to false for automated snapshot on destruction
  deletion_protection = false

  backup_retention_period = 7
  backup_window           = "03:00-04:00"

  tags = {
    Name = "${var.environment}-leetcode-postgres"
  }
}
