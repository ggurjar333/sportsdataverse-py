# Always prefer setuptools over distutils
# To use a consistent encoding
from codecs import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

extras = {
    "tests": [
        "black>=22.3.0",
        "flake8>=5.0.0",
        "isort>=5.10.1",
        "mypy>=0.782",
        "pycln>=2.1.6",
        "pydocstyle>=6.3.0",
        "pytest>=6.0.2",
        "pytest-cov>=2.10.1",
        "pytest-xdist>=2.1.0",
    ],
    "docs": ["sphinx"],
    "models": [
        "beautifulsoup4>=4.4.0",
        "inflection>=0.5.1",
        "requests>=2.18.1",
        "lxml>=4.2.1",
        "pyarrow>=1.0.1",
        "pyjanitor>=0.23.1",
        "pyreadr>=0.4.0",
        "scipy>=1.4.0",
        "matplotlib>=2.0.0",
        "tqdm>=4.50.0",
        "attrs>=20.3.0",
        "xgboost>=1.2.0",
    ],
}

extras["all"] = extras["tests"] + extras["docs"] + extras["models"]

setup(
    name="sportsdataverse",
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version="0.0.39",
    description="Retrieve Sports data in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # The project's main homepage.
    url="https://github.com/sportsdataverse/sportsdataverse-py",
    project_urls={
        "Docs": "https://py.sportsdataverse.org/",
        "Bug Tracker": "https://github.com/sportsdataverse/sportsdataverse-py/issues",
    },
    # Author details
    author="Saiem Gilani",
    author_email="saiem.gilani@gmail.com",
    # Maintainer
    maintainer="Saiem Gilani",
    # Choose your license
    license="MIT",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 3 - Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: MIT License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    # What does your project relate to?
    keywords="nfl college football data epa statistics web scraping",
    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=["tests", "tests.*"]),
    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],
    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        "numpy>=1.13.0",
        "pandas>= 1.0.3",
        "polars<=0.18.15",
        "tqdm>=4.50.0",
        "beautifulsoup4>=4.4.0",
        "inflection>=0.5.1",
        "requests>=2.18.1",
        "lxml>=4.2.1",
        "pyarrow>=8.0.0",
        "pyjanitor>=0.23.1",
        "pyreadr>=0.4.9",
        "scipy>=1.4.0",
        "matplotlib>=2.0.0",
        "attrs>=20.3.0",
        "xgboost>=1.2.0",
    ],
    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require=extras,
    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    include_package_data=True,
    package_data={
        "sportsdataverse": [
            "cfb/models/*",
            "nfl/models/*",
        ]
    },
    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    # entry_points={
    #    'console_scripts': [
    #        'sample=sample:main',
    #    ],
    # },
)
