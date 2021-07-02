from functools import wraps


def pip(libraries):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            import subprocess
            import sys

            for library, version in libraries.items():
                print('Pip Install:', library, version)
                subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', library + '==' + version])
            return function(*args, **kwargs)

        return wrapper

    return decorator


def enable_decorator(dec, flag):
    def decorator(func):
        if flag:
            return dec(func)
        return func
    return decorator
