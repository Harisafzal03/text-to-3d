from setuptools import setup, find_packages

setup(
    name="text-to-3d",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "torch>=1.8.0",
        "transformers>=4.5.0",
        "numpy>=1.20.0",
        "matplotlib>=3.4.0",
        "nltk>=3.6.0",
        "tqdm>=4.60.0",
    ],
    author="Text to 3D Developer",
    description="A model that converts text to 2D layout then to 3D model",
    keywords="text-to-3d, layout, generation, 3d-models",
    python_requires=">=3.8",
)