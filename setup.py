from pathlib import Path
from setuptools import setup, find_packages

setup(
    name="argus-osint",
    version="1.0.0",
    author="Gabriel Ramos",
    description="OSINT Suite com análise por IA",
    packages=find_packages(),
    install_requires=Path("requirements.txt").read_text(encoding="utf-8").splitlines(),
    entry_points={
        "console_scripts": [
            "argus=argus:app",
        ],
    },
    python_requires=">=3.10",
)
