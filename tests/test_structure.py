"""Test to verify project structure"""
import os
import pytest


def test_app_directory_exists():
    """Verify app directory exists"""
    assert os.path.exists("app"), "app directory should exist"
    assert os.path.exists("app/__init__.py"), "app/__init__.py should exist"
    assert os.path.exists("app/main.py"), "app/main.py should exist"


def test_lambda_directory_exists():
    """Verify lambda directory exists"""
    assert os.path.exists("lambda"), "lambda directory should exist"
    assert os.path.exists("lambda/requirements.txt"), "lambda/requirements.txt should exist"


def test_infrastructure_directory_exists():
    """Verify infrastructure directory exists"""
    assert os.path.exists("infrastructure"), "infrastructure directory should exist"
    assert os.path.exists("infrastructure/docker"), "infrastructure/docker should exist"
    assert os.path.exists("infrastructure/terraform"), "infrastructure/terraform should exist"


def test_docs_directory_exists():
    """Verify docs directory exists"""
    assert os.path.exists("docs"), "docs directory should exist"


def test_required_files_exist():
    """Verify required root files exist"""
    assert os.path.exists("README.md"), "README.md should exist"
    assert os.path.exists("requirements.txt"), "requirements.txt should exist"
    assert os.path.exists("PROJECT_STRUCTURE.md"), "PROJECT_STRUCTURE.md should exist"


def test_dockerfile_exists():
    """Verify Dockerfile exists in correct location"""
    assert os.path.exists("infrastructure/docker/Dockerfile"), "Dockerfile should exist in infrastructure/docker/"


def test_terraform_files_exist():
    """Verify Terraform files exist"""
    assert os.path.exists("infrastructure/terraform/main.tf"), "main.tf should exist"
    assert os.path.exists("infrastructure/terraform/variables.tf"), "variables.tf should exist"
    assert os.path.exists("infrastructure/terraform/outputs.tf"), "outputs.tf should exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
