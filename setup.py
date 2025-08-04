"""
업비트 자동매매 시스템 설치 스크립트
"""

from setuptools import setup, find_packages

setup(
    name="upbit-auto-trading",
    version="1.0.0",
    description="업비트 자동매매 시스템",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.9.1",
        "pandas>=2.0.3",
        "numpy>=1.24.4",
        "pyyaml>=6.0.1",
        "loguru>=0.7.0",
        "pytest>=7.4.0",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.11.1",
    ],
    package_data={
        "upbit_auto_trading": ["**/*.qss", "**/*.yaml", "**/*.sql"],
    },
    include_package_data=True,
)
