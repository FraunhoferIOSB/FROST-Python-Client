import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
info = {}
with open(os.path.join(here, 'frost_sta_client', '__version__.py')) as f:
    exec(f.read(), info)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name=info['__title__'],
    version=info['__version__'],
    description=info['__description__'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=info['__author__'],
    author_email=info['__contact__'],
    license=info['__license__'],
    url=info['__url__'],
    packages=find_packages(),
    install_requires=['demjson3>=3.0.5', 'furl>=2.1.3', 'geojson>=2.5.0', 'jsonpickle>=2.0.0', 'requests>=2.26.0',
                      'jsonpatch', 'python-dateutil'],
    keywords=['sta', 'ogc', 'frost', 'sensorthingsapi', 'IoT']
)
