class UnitOfMeasurement:
    def __init__(self,
                 name="",
                 symbol="",
                 definition=""):
        self.name = name
        self.symbol = symbol
        self.definition = definition

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if type(value) != str:
            raise ValueError('name should be of type str!')
        self._name = value

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self, value):
        if type(value) != str:
            raise ValueError('symbol should be of type str!')
        self._symbol = value

    @property
    def definition(self):
        return self._definition

    @definition.setter
    def definition(self, value):
        if type(value) != str:
            raise ValueError('definition should be of type str!')
        self._definition = value

    def __getstate__(self):
        data = {
            'symbol': self._symbol,
            'definition': self._definition,
            'name': self._name
        }
        return data

    def __setstate__(self, state):
        self.symbol = state.get("symbol", None)
        self.definition = state.get("definition", None)
        self.name = state.get("name", None)
