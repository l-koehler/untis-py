from setuptools import setup, find_packages

setup(
    name="untis-py",
    version="1.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests',
        'pyqt6',
        'python-dateutil',
        'webuntis',
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
