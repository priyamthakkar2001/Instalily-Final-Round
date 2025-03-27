from setuptools import setup, find_packages

setup(
    name="pool_equipment_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot>=20.0",
        "fastapi>=0.95.0",
        "uvicorn>=0.22.0",
        "pydantic>=2.0.0",
        "requests>=2.28.0",
        "python-dotenv>=1.0.0",
        "crewai>=0.28.0",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.2",
        "openai>=1.5.0",
        "tenacity>=8.2.0",
        "loguru>=0.7.0",
    ],
    python_requires=">=3.8",
)
