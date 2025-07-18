from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="loxprox",
    version='0.2.0',
    description='Modular UDP proxy for Loxone home automation - routes data to Philips Hue, monitoring systems, and more',
    author='Kevin Bortis',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'loxprox=loxprox.main:main',
            ],
        },
    python_requires='>=3.8',
)