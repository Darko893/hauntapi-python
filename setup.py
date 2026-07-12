from setuptools import setup

setup(
    name="hauntapi",
    version="1.1.0",
    description="Extract structured data from permitted public pages with one API call. Haunt API Python SDK.",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Haunt API",
    author_email="hello@hauntapi.com",
    url="https://hauntapi.com",
    py_modules=["hauntapi"],
    install_requires=[
        "httpx>=0.24.0",
    ],
    extras_require={
        "langchain": ["langchain-core>=0.2"],
        "llamaindex": ["llama-index-core>=0.10"],
        "crewai": ["crewai>=0.30"],
    },
    keywords="web-scraping web-extraction ai-agent agent-tools mcp langchain llamaindex crewai url-to-json url-to-markdown structured-data rag",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
