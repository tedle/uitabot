class HTTPException(Exception):
    text: str


class Forbidden(HTTPException):
    ...
