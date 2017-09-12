import setuptools

setuptools.setup(
    name = "sreinventory",
    version = "0.0.1",

    description = "SRE host, role, and service inventory",
    author = "Daniel Parks",
    author_email = "daniel.parks@puppet.com",
    url = "http://github.com/puppetlabs/sreinventory",
    long_description = open("README.rst").read(),

    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
    ],

    packages = [ "sreinventory" ],
    install_requires = [
        "Jinja2",
        "markdown2",
        "pygments",
        "simplepup"
    ],

    include_package_data = True,
    entry_points = {
        "console_scripts": [
            "sreinventory = sreinventory.cli:main"
        ]
    }
)
