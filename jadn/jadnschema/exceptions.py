"""
JADN Exceptions
"""
from builtins import BaseException, Exception


class FormatError(Exception):
    """
    JADN Syntax Error
    """


class OptionError(Exception):
    """
    JADN Field/Type option Error
    """