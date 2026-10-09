"""Typed errors safe to display at adapter boundaries."""


class ComposeError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
