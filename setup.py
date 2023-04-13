from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="loxprox",
    version='0.1.0',
    description='Control Philips Hue lights from Loxone Miniserver',
    author='Kevin Bortis',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'loxprox=loxprox.main:main',
            ],
        },
)