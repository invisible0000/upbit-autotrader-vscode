from setuptools import setup, find_packages

setup(
    name='upbit-autotrader',
    version='1.0.0',
    description='Upbit Autotrader: 실시간 암호화폐 자동매매 시스템 (데스크탑/웹/CLI 통합)',
    author='invisible0000',
    packages=find_packages(),
    install_requires=[
        # requirements.txt에서 자동 로드
    ],
    python_requires='>=3.8',
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'upbit-autotrader=upbit_auto_trading.__main__:main',
            'upbit-autotrader-desktop=upbit_auto_trading.ui.desktop.main:main',
            'upbit-autotrader-web=upbit_auto_trading.ui.web.main:main',
            'upbit-autotrader-cli=upbit_auto_trading.ui.cli.main:main',
        ],
    },
)
