class _InnerStateAccessor:
    def __getattr__(self, key):
        try:
            return self._inner_state[key]
        except KeyError:
            # Reset traceback before raising
            raise AttributeError(key) from None


class Scenario(_InnerStateAccessor):
    def __init__(self, name, description=None):
        if description is None:
            description = name

        self._inner_state = {
            'name': name,
            'description': description,
            'arguments': {},
            'constants': {},
            'openbach_functions': [],
        }

    def add_argument(self, name, description):
        self.arguments[name] = description

    def remove_argument(self, name):
        arguments = self.arguments
        try:
            del arguments[name]
        except KeyError:
            pass

    def add_constant(self, name, value):
        self.constants[name] = value

    def remove_constants(self, name):
        constants = self.contants
        try:
            del constants[name]
        except KeyError:
            pass

    def add_function(self, name, wait_delay=0, wait_launched=None, wait_finished=None):
        wait_launched = _check_and_build_waiting_list(wait_launched)
        wait_finished = _check_and_build_waiting_list(wait_finished)

        n = ''.join(name.title().split('_')) if '_' in name else name
        try:
            factory = globals()['_{}Function'.format(n)]
        except KeyError:
            # Reset traceback before raising
            raise ValueError('{} is not a valid OpenBach function'.format(n)) from None
        function = factory(wait_launched, wait_finished, wait_delay)
        self.openbach_functions.append(function)
        return function

    def remove_function(self, function):
        functions = self.openbach_functions
        try:
            functions.remove(function)
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


def _check_and_build_waiting_list(wait_on=None):
    if wait_on is None:
        wait_on = []
    else:
        wait_on = list(wait_on)

    for obj in wait_on:
        try:
            check_passed = obj.is_function()
        except (AttributeError, TypeError):
            check_passed = False
        if not check_passed:
            raise TypeError('can only wait on iterables of openbach functions')

    return wait_on


def _safe_indexor(reference, lookup):
    for element in lookup:
        try:
            yield reference.index(element)
        except ValueError:
            pass


class ImproperlyConfiguredFunction(Exception):
    def __init__(self, name):
        super().__init__('{} has not been configured yet'.format(name))


class _OpenBachFunction(_InnerStateAccessor):
    def __init__(self, launched, finished, delay):
        self._inner_state = {
            'wait': {
                'time': delay,
                'launched_indexes': launched,
                'finished_indexes': finished,
            },
        }

    def is_function(self):
        return True

    def build(self, functions):
        context = {'wait': {'time': self.wait['time']}}
        context['wait']['launched_indexes'] = list(
                _safe_indexor(functions, self.wait['launched_indexes']))
        context['wait']['finished_indexes'] = list(
                _safe_indexor(functions, self.wait['finished_indexes']))
        return context


class _StartJobInstanceFunction(_OpenBachFunction):
    def __init__(self, launched, finished, delay):
        super().__init__(launched, finished, delay)
        self._inner_state['start_job_instance'] = {}
        self._job_name = None

    def configure(self, job_name, agent_ip, offset=0, **job_arguments):
        arguments = self._inner_state['start_job_instance']
        arguments.clear()
        arguments['agent_ip'] = agent_ip
        arguments['offset'] = offset
        arguments[job_name] = job_arguments
        self._job_name = job_name

    def build(self, functions):
        if self._job_name is None:
            raise ImproperlyConfiguredFunction('start_job_instance')

        context = super().build(functions)

        job = self._job_name
        function = self.start_job_instance
        context['start_job_instance'] = {
            'agent_ip': function['agent_ip'],
            'offset': function['offset'],
            job: function[job].copy()
        }

        return context


class _StopJobInstanceFunction(_OpenBachFunction):
    def __init__(self, launched, finished, delay):
        super().__init__(launched, finished, delay)
        self._inner_state['stop_job_instance'] = {
            'openbach_function_indexes': (),
        }

    def configure(self, *functions):
        self.stop_job_instance['openbach_function_indexes'] = functions

    def build(self, functions):
        arguments = self.stop_job_instance['openbach_function_indexes']

        context = super().build(functions)
        context['stop_job_instance'] = {
            'openbach_function_indexes': list(
                _safe_indexor(functions, arguments))}
        return context
