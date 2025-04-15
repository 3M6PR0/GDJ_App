from setuptools import setup, find_packages

setup(
    name="mon_app",
    version="1.0.10",
    packages=find_packages(),
    install_requires=[
        "PyQt5",
    ],
    entry_points={
        "console_scripts": [
            "mon_app = main:main",
        ],
    },
)
