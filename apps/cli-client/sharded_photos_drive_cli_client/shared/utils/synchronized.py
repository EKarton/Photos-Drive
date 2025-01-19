import functools
import threading
from typing import Optional


def synchronized(lock: Optional[threading.RLock] = None):
    '''
    Decorates a function so that it runs in sync.

    Helpful for when you want to have a function that can only execute one
    at a time when multiple threads are calling this function.

    Functions decorated with this decorator that share the same lock
    can only be called one at a time.

    Args:
        lock (threading.Lock): [Optional] A lock

    Returns:
        function decorator
    '''
    if lock is None:
        lock = threading.RLock()

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)

        return wrapper

    return decorator
