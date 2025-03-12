import inspect


def inspect_func_params(func, *args, **kwargs):
    signature = inspect.signature(func)
    arguments = signature.bind(*args, **kwargs).arguments
    return {k: v for k, v in arguments.items()}
