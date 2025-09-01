#!/usr/bin/env python3
"""
Setup script for Papers Database
A scientific literature management system
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="papers-database",
    version="1.0.0",
    author="João Ribeiro",
    author_email="joaoribeiro@brainingai.com",
    description="A powerful desktop application for managing scientific papers",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="[your-repository-url]",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Education",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "papers-db=app.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="scientific papers, literature management, research, academic, pdf, database",
    project_urls={
        "Bug Reports": "[your-issues-url]",
        "Source": "[your-repository-url]",
        "Documentation": "[your-docs-url]",
    },
)
