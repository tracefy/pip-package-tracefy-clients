from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='pip_package_tracefy_clients',
    version='0.0.1',
    packages=find_packages(),
    install_requires=required
)
