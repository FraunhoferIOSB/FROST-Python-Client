import os
from setuptools import setup

# If build on GitLab-CI add dev and pipeline id as prefix to the version, to have a unique artifact
ci_pipeline_ID = os.environ.get('CI_PIPELINE_ID')
if ci_pipeline_ID:
    VERSION = "1.1.1" + ".dev" + ci_pipeline_ID
else:
    VERSION = "1.1.1"

setup(
    name='frost_sta_client',
    version=VERSION,
    description='a client library to facilitate interaction with a FROST SensorThings API Server',
    author='Katharina Emde',
    author_email='katharina.emde@iosb.fraunhofer.de',
    packages=['frost_sta_client', 'frost_sta_client/dao',
              'frost_sta_client/model', 'frost_sta_client/query', 'frost_sta_client/service',
              'frost_sta_client/model/ext'],
    install_requires=['jsonpickle', 'demjson', 'requests', 'furl', 'geojson'],
    key_words=['sta', 'ogc', 'frost']
)
