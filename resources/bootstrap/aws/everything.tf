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

resource "aws_s3_bucket" "terraform-state" {
  bucket = "${var.bucket_name}"

  /*object_lock_enabled = true*/

  /* If this is false, then the bucket can only be deleted when empty */
  force_destroy = false

  tags = {
    Name = "${var.bucket_name}"
    Environment = "${var.environment}"
  }
}
/*
resource "aws_s3_bucket_acl" "terraform-state" {
  bucket = aws_s3_bucket.terraform-state.id
  acl    = "private"
}
*/
/*
resource "aws_s3_bucket_object_lock_configuration" "terraform-state" {
  bucket = aws_s3_bucket.terraform-state.id
  rule {
    object_lock_enabled = "Enabled"
  }
}
*/
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform-state" {
  bucket = aws_s3_bucket.terraform-state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "terraform-state" {
  bucket = aws_s3_bucket.terraform-state.id
  versioning_configuration {
    status = "Enabled"
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
