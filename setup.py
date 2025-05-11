from setuptools import setup, find_packages

setup(
    name="untis-py",
    version="1.1.0",
    packages=find_packages(),
    include_package_data=True,
    # shouldn't be needed for the flake
    install_requires=[
        "python-dateutil",
        "webuntis",
    ],
    entry_points={
        "console_scripts": [
            "untis = untis_py.main:main"
        ]
    },
    package_data={
        "untis-py": ["icons/*.png", "icons/*.svg", "icons/*.ico"]
    },
)
