"""
Shared Module Setup
===================

Setup script for the shared utilities module.
"""

from setuptools import setup, find_packages

setup(
    name="shared",
    version="1.0.0",
    description="Shared utilities for microservices platform",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.0",
        "pydantic>=2.0.0",
        "redis>=5.0.0",
        "prometheus-client>=0.19.0",
        "opentelemetry-api>=1.21.0",
        "opentelemetry-sdk>=1.21.0",
        "opentelemetry-instrumentation-fastapi>=0.42b0",
        "opentelemetry-exporter-jaeger>=1.21.0",
    ],
)
