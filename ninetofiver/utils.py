from importlib import import_module


def str_import(string):
    """Import a class from a string."""
    module, attr = string.rsplit('.', maxsplit=1)
    module = import_module(module)
    attr = getattr(module, attr)

    return attr
