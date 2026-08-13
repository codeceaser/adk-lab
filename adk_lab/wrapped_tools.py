from functools import wraps
from typing import Callable

from .tools import get_assessment_unit


def preserve_metadata_wrapper(func: Callable) -> Callable:
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapped


wrapped_get_assessment_unit = preserve_metadata_wrapper(
    get_assessment_unit
)