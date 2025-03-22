from setuptools import setup, find_packages

setup(
    name="supa-maid-bot",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["bot"],
    entry_points={
        "console_scripts": [
            "supa-maid-bot=bot:main",
        ],
    },
)