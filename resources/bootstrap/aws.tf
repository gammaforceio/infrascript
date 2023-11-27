variable "bucket_name" {
  type = string
  nullable = false
}
variable "environment" {
  type = string
  nullable = false
}
variable "dynamodb_table" {
  type = string
  nullable = false
}
variable "region" {
  type = string
  nullable = false
}

provider aws {
  region = var.region
}

resource "aws_s3_bucket" "terraform-state" {
  bucket = "${var.bucket_name}"

  force_destroy = false

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  object_lock_configuration {
    object_lock_enabled = "Enabled"
  }

  tags = {
    Name = "${var.bucket_name}"
    Environment = "${var.environment}"
  }
}
resource "aws_dynamodb_table" "terraform-lock" {
  name           = "${var.dynamodb_table}"
  read_capacity  = 2
  write_capacity = 2
  hash_key       = "LockID"
  attribute {
    name = "LockID"
    type = "S"
  }
  tags = {
    Name = "Terraform State Lock Table for ${var.environment}"
    Environment = "${var.environment}"
  }
}

output "region" {
  value = var.region
}
output "bucket_name" {
  value = var.bucket_name
}
output "dynamodb_table" {
  value = var.dynamodb_table
}
