import pytest

from repogpt.file_handler.abstract_handler import CodeType, ParsedCode
from repogpt.file_handler.terraform_file_handler import TerraformModuleExtractor

# Initialize the TerraformModuleExtractor handler
handler = TerraformModuleExtractor()

# Sample inputs and expected outputs for different types
SAMPLE_MODULE_INPUT_TEXT = """
module "sample_module" {
  source = "./modules/sample_module"
  version = "1.0.0"
}
"""

EXPECTED_MODULE_PARSED_CODE = [
    ParsedCode(
        function_name="sample_module",
        class_name=None,
        code_type=CodeType.MODULE,
        code='module "sample_module" {\n  source = "./modules/sample_module"\n  version = "1.0.0"\n}',
        summary=None,
        inputs=None,
        outputs=None,
    )
]

SAMPLE_PROVIDER_INPUT_TEXT = """
provider "aws" {
  region = "us-west-2"
}
"""

EXPECTED_PROVIDER_PARSED_CODE = [
    ParsedCode(
        function_name="aws",
        class_name=None,
        code_type=CodeType.PROVIDER,
        code='provider "aws" {\n  region = "us-west-2"\n}',
        summary=None,
        inputs=None,
        outputs=None,
    )
]

SAMPLE_VARIABLE_INPUT_TEXT = """
variable "instance_type" {
  type = string
  default = "t2.micro"
}
"""

EXPECTED_VARIABLE_PARSED_CODE = [
    ParsedCode(
        function_name="instance_type",
        class_name=None,
        code_type=CodeType.VARIABLE,
        code='variable "instance_type" {\n  type = string\n  default = "t2.micro"\n}',
        summary=None,
        inputs=None,
        outputs=None,
    )
]

SAMPLE_OUTPUT_INPUT_TEXT = """
output "instance_ip" {
  value = aws_instance.web.public_ip
}
"""

EXPECTED_OUTPUT_PARSED_CODE = [
    ParsedCode(
        function_name="instance_ip",
        class_name=None,
        code_type=CodeType.OUTPUT,
        code='output "instance_ip" {\n  value = aws_instance.web.public_ip\n}',
        summary=None,
        inputs=None,
        outputs=None,
    )
]

SAMPLE_DATA_INPUT_TEXT = """
data "aws_ami" "latest" {
  most_recent = true
  owners      = ["self"]
}
"""

EXPECTED_DATA_PARSED_CODE = [
    ParsedCode(
        function_name="latest",
        class_name=None,
        code_type=CodeType.DATA,
        code='data "aws_ami" "latest" {\n  most_recent = true\n  owners      = ["self"]\n}',
        summary=None,
        inputs=None,
        outputs=None,
    )
]

SAMPLE_LOCAL_INPUT_TEXT = """
locals {
  service_name = "forum"
  owner        = "Community Team"
}
"""

EXPECTED_LOCAL_PARSED_CODE = [
    ParsedCode(
        function_name=None,
        class_name=None,
        code_type=CodeType.LOCALS,
        code='locals {\n  service_name = "forum"\n  owner        = "Community Team"\n}',
        summary=None,
        inputs=None,
        outputs=None,
    )
]


@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        (SAMPLE_MODULE_INPUT_TEXT, EXPECTED_MODULE_PARSED_CODE),
        (SAMPLE_PROVIDER_INPUT_TEXT, EXPECTED_PROVIDER_PARSED_CODE),
        (SAMPLE_VARIABLE_INPUT_TEXT, EXPECTED_VARIABLE_PARSED_CODE),
        (SAMPLE_OUTPUT_INPUT_TEXT, EXPECTED_OUTPUT_PARSED_CODE),
        (SAMPLE_DATA_INPUT_TEXT, EXPECTED_DATA_PARSED_CODE),
        (SAMPLE_LOCAL_INPUT_TEXT, EXPECTED_LOCAL_PARSED_CODE),
        # Add other test cases here
    ],
)
def test_normal_operation(tmp_path, input_text, expected_output):
    p = tmp_path / "test_terraform_file.tf"
    p.write_text(input_text)
    parsed_code = handler.extract_code(p)

    assert isinstance(parsed_code, list)
    assert all(isinstance(code, ParsedCode) for code in parsed_code)
    parsed_code.sort()
    expected_output.sort()
    assert len(parsed_code) == len(expected_output)
    assert parsed_code == expected_output


def test_no_module_in_file(tmp_path):
    p = tmp_path / "no_module_terraform_file.tf"
    code = """
    some random text
  type = string
  default = "t2.micro"
}
"""
    p.write_text(code)
    parsed_code = handler.extract_code(p)
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 0


def test_edge_cases(tmp_path):
    # Test empty Terraform file
    p = tmp_path / "empty_terraform_file.tf"
    p.write_text("")
    parsed_code = handler.extract_code(p)
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 0

    # Test non-Terraform file
    p = tmp_path / "non_terraform_file.txt"
    text = "This is a text file, not a Terraform file."
    p.write_text(text)
    parsed_code = handler.extract_code(p)
    assert len(parsed_code) == 0

    # Test non-existent file
    p = tmp_path / "non_existent_file.tf"
    with pytest.raises(FileNotFoundError):
        handler.extract_code(p)
