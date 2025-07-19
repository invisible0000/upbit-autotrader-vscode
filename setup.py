from setuptools import setup, find_packages

# Read version from version.json
import json
import os

def read_version():
    """Read version information from version.json"""
    version_file = os.path.join(os.path.dirname(__file__), 'version.json')
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
            return version_data['version']
    return "0.1.0-alpha"

def read_readme():
    """Read README.md for long description"""
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "Advanced cryptocurrency autotrading system for Upbit exchange"

setup(
    name="upbit-autotrader-vscode",
    version=read_version(),
    description="Advanced cryptocurrency autotrading system for Upbit exchange with optimized chart visualization",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Upbit Autotrader Development Team",
    author_email="dev@upbit-autotrader.com",
    url="https://github.com/invisible0000/upbit-autotrader-vscode",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.5.0",
        "pyqtgraph>=0.13.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "cryptography>=41.0.0",
        "pyjwt>=2.8.0",  # 필수! JWT 토큰 처리용
        "pyyaml>=6.0.0",
        "websockets>=11.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-qt>=4.2.0",
            "flake8>=6.0.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-qt>=4.2.0",
            "pytest-cov>=4.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "upbit-autotrader=upbit_auto_trading.__main__:main",
            "upbit-gui=run_desktop_ui:main",
            "upbit-test=run_tests_in_order:main",
        ],
    },
    include_package_data=True,
    package_data={
        "upbit_auto_trading": [
            "ui/desktop/styles/*.qss",
            "ui/desktop/assets/*",
            "config/*.yaml",
            "data/*.sql",
        ],
    },
    keywords=[
        "upbit", "cryptocurrency", "autotrading", "chart", "PyQt6", 
        "trading-bot", "bitcoin", "ethereum", "real-time", "websocket"
    ],
    project_urls={
        "Bug Reports": "https://github.com/invisible0000/upbit-autotrader-vscode/issues",
        "Source": "https://github.com/invisible0000/upbit-autotrader-vscode",
        "Documentation": "https://github.com/invisible0000/upbit-autotrader-vscode/wiki",
        "Changelog": "https://github.com/invisible0000/upbit-autotrader-vscode/blob/main/CHANGELOG.md",
    },
)
