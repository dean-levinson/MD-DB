import setuptools


setuptools.setup(
    name="md_client",
    version="0.0.1",
    package_dir={"": "."},
    packages=setuptools.find_packages(),
    python_requires=">=3.10",
    entry_points={
        'console_scripts': [
            'md_client = md_client.main:main',
        ],
    },
)