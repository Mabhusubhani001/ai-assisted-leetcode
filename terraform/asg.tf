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

              # 1. Update OS and install Docker + Git
              dnf update -y
              dnf install -y docker git
              systemctl enable docker
              systemctl start docker
              usermod -a -G docker ec2-user

              # 2. Install Docker Compose plugin
              mkdir -p /usr/local/lib/docker/cli-plugins
              curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
              chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

              echo "EC2 Instance successfully provisioned for DSA Assessment Platform."
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

  min_size         = var.asg_min_size
  max_size         = var.asg_max_size
  desired_capacity = var.asg_desired_capacity

  health_check_type         = "ELB"
  health_check_grace_period = 300

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
              dnf update -y
              dnf install -y docker git
              systemctl enable docker
              systemctl start docker
              EOF
  )

  tags = {
    Name = "${var.environment}-judge0-sandbox-instance"
  }
}
