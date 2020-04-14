#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("requirements_dashboard.txt") as requirements_file:
    requirements = requirements_file.readlines()

setup_requirements = []

test_requirements = []

setup(
    author="Sebastian Weigand",
    author_email="s.weigand.phy@gmail.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description=(
        "scraper, analysis and dashboard code "
        "to get an introspective to the current covid19 data"
    ),
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="covid19_data_analyzer",
    name="covid19_data_analyzer",
    packages=find_packages(
        include=["covid19_data_analyzer", "covid19_data_analyzer.*"]
    ),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/s-weigand/covid19-data-analyzer",
    project_urls={
        "Documentation": "https://covid19-data-analyzer.readthedocs.io/",
        "Source": "https://github.com/s-weigand/covid19-data-analyzer",
        "Tracker": "https://github.com/s-weigand/covid19-data-analyzer/issues",
    },
    platforms="any",
    entry_points={
        "console_scripts": [
            "covid19_dashboard = covid19_data_analyzer.dashboard.index:run_dashboard_server",
        ]
    },
    version="0.1.0",
    zip_safe=False,
)
