output "vpc_id" {
  description = "ID of the SecureVPC VPC."
  value       = aws_vpc.securevpc.id
}

output "vpc_cidr" {
  description = "CIDR range of the SecureVPC."
  value       = aws_vpc.securevpc.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets."
  value       = aws_subnet.private[*].id
}
