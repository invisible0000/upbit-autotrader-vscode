from setuptools import setup, find_packages

setup(
    name="upbit_auto_trading",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "requests",
        "python-dotenv",
    ],
)
