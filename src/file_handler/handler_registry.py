handler_registry = {}


def register_handler(ext):
    def decorator(cls):
        handler_registry[ext] = cls
        return cls

    return decorator
