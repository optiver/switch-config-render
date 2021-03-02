
from setuptools import setup, find_packages


with open("README.md") as fh:
    long_description = fh.read()

setup(
    name="switch-config-render",
    version="0.2.0",
    description="A Python library for SVG network switch configuration rendering.",
    long_description=long_description,
    author="Josef Schneider",
    author_email="josef.schneider@optiver.com.au",
    packages=find_packages(),
    install_requires=["svgwrite"],
    extras_require={"test": ["pytest", "pytest-cov"]},
    classifiers=[
         "License :: OSI Approved :: Apache Software License",
         "Operating System :: OS Independent",
         "Programming Language :: Python :: 2.7",
         "Programming Language :: Python :: 3",
         "Programming Language :: Python :: 3.5",
         "Programming Language :: Python :: 3.6",
         "Intended Audience :: Developers",
         "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)
