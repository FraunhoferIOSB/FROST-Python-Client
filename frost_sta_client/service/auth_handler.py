from requests.auth import HTTPBasicAuth


class AuthHandler:
    def __init__(self, username="", password=""):
        self.username = username
        self.password = password

    def add_auth_header(self):
        if not (self.username is None or self.password is None):
            return HTTPBasicAuth(self.username, self.password)


