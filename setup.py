from setuptools import setup, find_packages

setup(
    name="argus-osint",
    version="1.0.0",
    author="Gabriel Ramos",
    description="OSINT Suite com análise por IA",
    packages=find_packages(),
    install_requires=open("requirements.txt").read().splitlines(),
    entry_points={
        "console_scripts": [
            "argus=argus:app",
        ],
    },
    python_requires=">=3.10",
)
