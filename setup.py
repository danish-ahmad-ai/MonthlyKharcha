from setuptools import setup, find_packages
import os

# Read README.md if it exists, otherwise use a basic description
long_description = "A modern expense tracking and roommate settlement manager"
if os.path.exists('README.md'):
    with open('README.md', 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name="monthly-kharcha",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'customtkinter>=5.2.0',
        'pandas>=1.5.0',
        'matplotlib>=3.7.0',
        'seaborn>=0.12.0',
        'scikit-learn>=1.0.0',
        'tkcalendar>=1.6.1',
        'reportlab>=3.6.12',
        'numpy>=1.21.0'
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A modern expense tracking and roommate settlement manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/monthly-kharcha",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'monthly-kharcha=monthly_kharcha.main:main',
        ],
    },
) 