import setuptools

setuptools.setup(
    name = "infinitory",
    version = "0.1.6",

    description = "SRE host, role, and service inventory",
    author = "Daniel Parks",
    author_email = "daniel.parks@puppet.com",
    url = "http://github.com/puppetlabs/infinitory",
    long_description = open("README.rst").read(),

    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
    ],

    packages = setuptools.find_packages(),
    install_requires = [
        "click",
        "Jinja2",
        "markdown2",
        "pygments",
        "simplepup",
        "pypuppetdb",
        "google-cloud-storage",
    ],

    tests_require = [
        "pytest",
    ],

    include_package_data = True,
    entry_points = {
        "console_scripts": [
            "infinitory = infinitory.cli:main"
        ]
    }
)
