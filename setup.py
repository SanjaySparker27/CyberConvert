#!/usr/bin/env python3
"""
Setup script for 3D File Format Converter
"""

from setuptools import setup, find_packages
import os

# Read requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read long description
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='converter3d',
    version='1.0.0',
    author='3D Converter Team',
    description='Universal 3D file format converter supporting 20+ formats',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/3d-converter',
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Manufacturing',
        'Topic :: Multimedia :: Graphics :: 3D Modeling',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'converter3d=converter3d.cli:main',
            '3dconvert=converter3d.cli:main',
        ],
        'gui_scripts': [
            'converter3d-gui=converter3d.gui:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
