from .openbach_functions import OpenBachFunction


class Scenario:
    def __init__(self, name, description=None):
        if description is None:
            description = name

        self.name = name
        self.description = description
        self.arguments = {}
        self.constants = {}
        self.openbach_functions = []

    def add_argument(self, name, description):
        self.arguments[name] = description

    def remove_argument(self, name):
        try:
            del self.arguments[name]
        except KeyError:
            pass

    def add_constant(self, name, value):
        self.constants[name] = value

    def remove_constants(self, name):
        try:
            del self.contants[name]
        except KeyError:
            pass

    def add_function(self, name, wait_delay=0, wait_launched=None, wait_finished=None):
        wait_launched = check_and_build_waiting_list(wait_launched)
        wait_finished = check_and_build_waiting_list(wait_finished)

        n = ''.join(name.title().split('_')) if '_' in name else name
        factory = get_function_factory(n)
        function = factory(wait_launched, wait_finished, wait_delay)
        self.openbach_functions.append(function)
        return function

    def remove_function(self, function):
        try:
            self.openbach_functions.remove(function)
        except ValueError:
            pass

    def build(self):
        openbach_functions = self.openbach_functions
        functions = [f.build(openbach_functions) for f in openbach_functions]
        return {
            'name': self.name,
            'description': self.description,
            'arguments': self.arguments.copy(),
            'constants': self.constants.copy(),
            'openbach_functions': functions,
        }


def check_and_build_waiting_list(wait_on=None):
    wait_on = [] if wait_on is None else list(wait_on)
    if not all(isinstance(obj, OpenBachFunction) for obj in wait_on):
        raise TypeError('can only wait on iterables of openbach functions')
    return wait_on


def get_function_factory(name):
    for cls in OpenBachFunction.__subclasses__():
        if cls.__name__ == name:
            return cls
    raise ValueError('{} is not a valid OpenBach function'.format(name))
