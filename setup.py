import os
import configparser
from setuptools import setup, find_packages

# Lire la version depuis data/version.txt
version_file = os.path.join(os.path.dirname(__file__), "data", "version.txt")
config = configparser.ConfigParser()
config.read(version_file, encoding="utf-8")
version = config.get("Version", "value").strip()

setup(
    name="mon_app",
    version=version,
    packages=find_packages(),
    install_requires=["PyQt5"],
    entry_points={
        "console_scripts": [
            "mon_app = main:main",
        ],
    },
)
