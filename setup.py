#!/usr/bin/env python3
"""
Setup script for the Hexapod Voice Control System.

A comprehensive autonomous control system for hexapod walking robots, featuring
real-time sound source localization, voice command recognition, and advanced
auditory scene analysis capabilities.
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="hexapod-voice-control",
    version="1.0.0",
    author="Krystian Głodek",
    author_email="krystian.glodek1717@gmail.com",
    description="Autonomous hexapod robot control system with voice commands and sound source localization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gl0dny/hexapod",
    project_urls={
        "Bug Reports": "https://github.com/gl0dny/hexapod/issues",
        "Source": "https://github.com/gl0dny/hexapod",
        "Documentation": "https://github.com/gl0dny/hexapod/blob/main/README.md",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Robotics",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: System :: Hardware :: Hardware Drivers",
    ],
    keywords=[
        "robotics", "hexapod", "voice-control", "sound-localization", 
        "picovoice", "odas", "audio-processing", "beamforming", 
        "directional-audio", "keyword-spotting", "speech-recognition",
        "autonomous-robots", "auditory-scene-analysis", "doa-estimation"
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
        "docs": [
            "sphinx",
            "sphinx-rtd-theme",
            "myst-parser",
        ],
    },
    entry_points={
        "console_scripts": [
            "hexapod=hexapod.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "hexapod": [
            "kws/porcupine/*.ppn",
            "kws/rhino/*.rhn",
            "kws/rhino/*.yml",
            "interface/logging/config/*.yaml",
            "robot/config/*.yaml",
            "robot/config/*.json",
            "odas/config/*.cfg",
        ],
    },
    data_files=[
        ("share/hexapod", ["README.md", "requirements.txt", "INSTALL.md", "DEPLOYMENT.md"]),
        ("share/hexapod/config", [".env.picovoice"]),
        ("share/hexapod/docs", ["docs/README.md"]),
    ],
    zip_safe=False,
    platforms=["Linux"],
    license="MIT",
)
