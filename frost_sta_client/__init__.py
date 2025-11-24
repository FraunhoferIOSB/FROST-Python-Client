import jsonpickle

# Configure jsonpickle backend
jsonpickle.load_backend('demjson3', 'encode', 'decode', 'JSONDecodeError')
jsonpickle.set_preferred_backend('demjson3')
jsonpickle.set_decoder_options('demjson3', decode_float=float)

from .__version__ import (
    __title__, __version__, __license__, __author__, __contact__, __url__,
    __description__, __copyright__
)
