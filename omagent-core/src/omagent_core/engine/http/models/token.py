class Token(object):
    swagger_types = {
        'token': 'str'
    }

    attribute_map = {
        'token': 'token'
    }

    def __init__(self, token: str = None):
        self.token = None
        if token is not None:
            self.token = token

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, token: str):
        self._token = token
