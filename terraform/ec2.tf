resource "aws_instance" "stockloom" {

  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  subnet_id = aws_subnet.public_subnet.id

  vpc_security_group_ids = [
    aws_security_group.stockloom_sg.id
  ]

  key_name = aws_key_pair.stockloom.key_name

  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  associate_public_ip_address = true

  user_data = file("userdata.sh")

  tags = merge(
    local.common_tags,
    {
      Name = local.instance_name
    }
  )

}