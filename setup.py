from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='TracefyClients',
    version='0.0.5',
    packages=find_packages(),
    install_requires=required
)
