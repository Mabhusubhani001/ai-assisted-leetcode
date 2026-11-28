# ----------------------------------------------------
# Amazon Linux 2023 AMI Data Source
# ----------------------------------------------------
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ----------------------------------------------------
# IAM Role & Instance Profile for EC2 Instances
# ----------------------------------------------------
resource "aws_iam_role" "ec2_role" {
  name = "${var.environment}-ec2-dsa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.environment}-ec2-dsa-profile"
  role = aws_iam_role.ec2_role.name
}

# ----------------------------------------------------
# EC2 Launch Template (Production Blueprint)
# ----------------------------------------------------
resource "aws_launch_template" "app" {
  name_prefix   = "${var.environment}-dsa-app-"
  image_id      = data.aws_ami.al2023.id
  instance_type = var.instance_type

  iam_instance_profile {
    arn = aws_iam_instance_profile.ec2_profile.arn
  }

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.app.id]
  }

  # Automated Instance Bootstrapping Script
  user_data = base64encode(<<-EOF
              #!/bin/bash
              set -ex

              # 1. Allocate 2GB Swap to ensure Next.js builds cleanly on t3.micro (1GB RAM)
              dd if=/dev/zero of=/swapfile bs=128M count=16
              chmod 600 /swapfile
              mkswap /swapfile
              swapon /swapfile
              echo "/swapfile swap swap defaults 0 0" >> /etc/fstab

              # 2. Update OS and install Docker + Git
              dnf update -y
              dnf install -y docker git
              systemctl enable docker
              systemctl start docker
              usermod -a -G docker ec2-user

              # 3. Install Docker Compose plugin
              mkdir -p /usr/local/lib/docker/cli-plugins
              curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
              chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

              # 4. Clone Application Codebase
              cd /home/ec2-user
              rm -rf app
              git clone https://github.com/Mabhusubhani001/ai-assisted-leetcode.git app
              cd app

              # 5. Generate Production .env with Live RDS Database Endpoint
              echo "ENVIRONMENT=production" > .env
              echo "DATABASE_URL=postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${var.db_name}" >> .env
              echo "REDIS_URL=redis://redis:6379/0" >> .env
              echo "QUESTION_TOKEN_LIMIT=2000" >> .env
              echo "GEMINI_API_KEY=" >> .env
              echo "GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/" >> .env
              echo "GEMINI_PRIMARY_MODEL=gemini-3.5-flash-lite" >> .env
              echo "GEMINI_FALLBACK_MODEL=gemini-3.1-flash-lite" >> .env
              echo "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_dG9waWNhbC1wcmF3bi0xNjcuY2xlcmsuYWNjb3VudHMuZGV2JA" >> .env
              echo "CLERK_SECRET_KEY=sk_test_dwlTxbPJ0AVgZITMFoZJ459VIVvH5lK9qKZipPP0EU" >> .env
              echo "CLERK_JWKS_URL=https://topical-prawn-167.clerk.accounts.dev/.well-known/jwks.json" >> .env
              echo "NEXT_PUBLIC_API_URL=" >> .env

              # 6. Build and launch production containers
              /usr/local/lib/docker/cli-plugins/docker-compose -f docker-compose.aws.yml up -d --build

              # 7. Apply Alembic Migrations and Seed Database Questions
              sleep 15
              docker exec leetcode_backend /opt/venv/bin/alembic upgrade head || true
              docker exec leetcode_backend /opt/venv/bin/python -m app.db.seed || true

              echo "DSA Assessment Platform deployment completed successfully."
              EOF
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.environment}-dsa-asg-worker"
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ----------------------------------------------------
# EC2 Auto Scaling Group (ASG)
# Spans 2 Private App Subnets across Availability Zones
# ----------------------------------------------------
resource "aws_autoscaling_group" "app" {
  name_prefix         = "${var.environment}-dsa-asg-"
  vpc_zone_identifier = aws_subnet.private[*].id

  min_size                  = var.asg_min_size
  max_size                  = var.asg_max_size
  desired_capacity          = var.asg_desired_capacity
  wait_for_capacity_timeout = "0"

  health_check_type         = "ELB"
  health_check_grace_period = 600

  target_group_arns = [
    aws_lb_target_group.frontend.arn,
    aws_lb_target_group.backend.arn,
  ]

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
    }
  }

  tag {
    key                 = "Name"
    value               = "${var.environment}-dsa-asg-node"
    propagate_at_launch = true
  }
}

# ----------------------------------------------------
# Auto Scaling Dynamic Policy (Target Tracking: 70% CPU)
# ----------------------------------------------------
resource "aws_autoscaling_policy" "cpu_target" {
  name                   = "${var.environment}-cpu-target-tracking"
  policy_type            = "TargetTrackingScaling"
  autoscaling_group_name = aws_autoscaling_group.app.name

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# ----------------------------------------------------
# Dedicated Judge0 Sandboxed Execution EC2 Instance (Conditional)
# ----------------------------------------------------
resource "aws_instance" "judge0" {
  count                  = var.enable_judge0 ? 1 : 0
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.judge0_instance_type
  subnet_id              = aws_subnet.private[0].id
  vpc_security_group_ids = [aws_security_group.judge0.id]

  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  user_data = base64encode(<<-EOF
              #!/bin/bash
              set -ex

              # 1. Allocate 2GB Swap space to ensure compilers (g++, javac) have memory buffer
              dd if=/dev/zero of=/swapfile bs=128M count=16
              chmod 600 /swapfile
              mkswap /swapfile
              swapon /swapfile
              echo "/swapfile swap swap defaults 0 0" >> /etc/fstab

              # 2. Update packages and install Docker + Git
              dnf update -y
              dnf install -y docker git
              systemctl enable docker
              systemctl start docker
              usermod -a -G docker ec2-user

              # 3. Install Docker Compose CLI plugin
              mkdir -p /usr/local/lib/docker/cli-plugins
              curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
              chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

              # 4. Clone repo and deploy Judge0 stack
              mkdir -p /home/ec2-user/judge0
              cd /home/ec2-user/judge0
              git clone https://github.com/Mabhusubhani001/ai-assisted-leetcode.git app
              cd app/deploy/judge0

              # 5. Launch Judge0 CE (Server, Worker, DB, Redis)
              /usr/local/lib/docker/cli-plugins/docker-compose -f docker-compose.judge0.yml up -d
              EOF
  )

  tags = {
    Name = "${var.environment}-judge0-sandbox-instance"
  }
}
