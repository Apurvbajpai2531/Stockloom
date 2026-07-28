output "instance_id" {
  value = aws_instance.stockloom.id
}

output "public_ip" {
  value = aws_eip.stockloom.public_ip
}

output "public_dns" {
  value = aws_instance.stockloom.public_dns
}

output "vpc_id" {
  value = aws_vpc.main.id
}