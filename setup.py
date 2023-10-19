from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = '0.0.1'
DESCRIPTION = ''

# Setting up
setup(
    name="nfoinstruments",
    version=VERSION,
    author="Ewout van der Veer",
    author_email="<ewout.van.der.veer@rug.nl>",
    description=DESCRIPTION,
    packages=find_packages(),
    install_requires=['pyvisa', 'pymeasure', 'tk'],
    keywords=['python', 'instrument', 'measure', 'measurement', 'experiment']
)