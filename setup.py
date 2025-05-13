from setuptools import setup, find_packages

setup(
    name="untis_py",
    version="1.1.0",
    packages=["untis_py"],
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
        "untis_py": ["icons/*.png", "icons/*.svg", "icons/*.ico"]
    },
    zip_safe=False
)
