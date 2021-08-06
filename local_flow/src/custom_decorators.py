"""

Custom decorators for use with Metaflow

"""
from typing import Dict, Optional, Any, Callable, TypeVar
from functools import wraps


RT = TypeVar('RT')  # return type


def pip(libraries: Dict[str, str]) -> Callable[[Callable[..., RT]], Callable[..., RT]]:
    def decorator(func: Callable[..., RT]) -> Callable[..., RT]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Dict[Any, Any]) -> RT:
            import subprocess
            import sys
            for library, version in libraries.items():
                print('Pip Install:', library, version)
                if version != '':
                    subprocess.run([sys.executable, '-m', 'pip',
                                   'install', library + '==' + version])
                else:
                    subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', library])
            return func(*args, **kwargs)

        return wrapper

    return decorator


def enable_decorator(dec: Callable[[Callable[..., RT]], Callable[..., RT]],
                     flag: Optional[Any] = False) -> Callable[[Callable[..., RT]], Callable[..., RT]]:
    try:
        flag = bool(int(flag))
    except Exception as e:
        flag = False
        print(e)

    def decorator(func: Callable[..., RT]) -> Callable[..., RT]:
        if flag:
            return dec(func)
        return func
    return decorator
