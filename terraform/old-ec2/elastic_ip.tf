resource "aws_eip" "stockloom" {

  domain = "vpc"

}

resource "aws_eip_association" "stockloom" {

  allocation_id = aws_eip.stockloom.id

  instance_id = aws_instance.stockloom.id

}