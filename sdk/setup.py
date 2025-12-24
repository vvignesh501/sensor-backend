"""
Setup configuration for Redlen Sensor SDK
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="redlen-sensor-sdk",
    version="1.0.0",
    author="Redlen Technologies",
    author_email="dev@redlen.com",
    description="Official Python SDK for Redlen Sensor API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/redlen/sensor-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "pydantic>=2.0.0",
        "urllib3>=1.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.990",
        ],
    },
    keywords="redlen sensor iot api sdk",
    project_urls={
        "Bug Reports": "https://github.com/redlen/sensor-sdk/issues",
        "Source": "https://github.com/redlen/sensor-sdk",
        "Documentation": "https://docs.redlen.com/sdk",
    },
)
