import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ronbun",
    version="0.1.0",
    author="The Renegade Coder",
    author_email="jeremy.grifski@therenegadecoder.com",
    description="The Sample Programs README Automation Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TheRenegadeCoder/sample-programs-readmes",
    packages=setuptools.find_packages(),
    install_requires=[
        "SnakeMD>=0",
        "subete>=0"
    ],
    entry_points={
        "console_scripts": [
            'ronbun = ronbun.readme:main'
        ],
    },
    classifiers=(
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License"
    ),
)
