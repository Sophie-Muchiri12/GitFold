from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="gitfold",
    version="0.1.0",
    author="Your Name",
    author_email="your@email.com",
    description="One command to stage, commit, merge, push, and open a PR — powered by AI.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gitfold",
    py_modules=["main", "git_handler", "ai_integration", "config_manager", "github_api", "logger"],
    python_requires=">=3.9",
    install_requires=[
        "gitpython",
        "openai",
        "requests",
        "python-dotenv",
        "click",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "gitfold=main:done",
            "gf=main:done",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    keywords="git automation ai commit pull-request developer-tools cli",
)