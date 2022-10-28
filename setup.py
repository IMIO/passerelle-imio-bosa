from setuptools import find_packages
from setuptools import setup

version = "1.0.2"

setup(
    name="passerelle-imio-apims-baec",
    version=version,
    author="iMio",
    author_email="support-ts@imio.be",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Environment :: Web Environment",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
    ],
    url="https://github.com/IMIO/passerelle-imio-apims-baec",
    install_requires=[
        "django>=2.2",
    ],
    zip_safe=False,
)
