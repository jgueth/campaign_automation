"""
Setup configuration for campaign_automation package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="campaign_automation",
    version="0.1.0",
    description="Campaign creative automation tools for multi-market campaign generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Jan Gueth",
    python_requires=">=3.7",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pyyaml>=5.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "campaign-validate=campaign_automation.campaign_validator:main",
            "campaign-generate-folders=campaign_automation.output_folder_generator:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
