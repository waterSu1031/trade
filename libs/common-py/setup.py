from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tradelib",
    version="0.1.0",
    author="Trade System Team",
    author_email="team@tradesystem.com",
    description="Common utilities for trade system microservices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/waterSu1031/trade",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "asyncpg>=0.29.0",
        "redis>=5.0.1",
        "ib_insync>=0.9.86",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
)