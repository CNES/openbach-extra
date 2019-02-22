from .conditions import Condition


class ImproperlyConfiguredFunction(Exception):
    """Exception raised when an openbach function that has not been
    configured yet is used to build a scenario.
    """

    def __init__(self, name):
        super().__init__('{} has not been configured yet'.format(name))


class OpenBachFunction:
    """Base class for every OpenBach functions.

    Define the common boilerplate necessary to build their
    representation.
    """

    def __init__(self, launched, finished, delay, label=None):
        self.time = delay
        self.wait_launched = launched
        self.wait_finished = finished
        self.label = label

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        return {
                'id': function_id,
                'label': self.label if self.label else '#{}'.format(function_id),
                'wait': {
                    'time': self.time,
                    'launched_ids': list(safe_indexor(functions, self.wait_launched)),
                    'finished_ids': list(safe_indexor(functions, self.wait_finished)),
                },
        }


class StartJobInstance(OpenBachFunction):
    """Representation of the start_job_instance openbach function."""

    def __init__(self, launched, finished, delay, label):
        super().__init__(launched, finished, delay, label)
        self.start_job_instance = {}
        self.job_name = None

    def configure(self, job_name, entity_name, offset=0, **job_arguments):
        """Define this openbach function with the mandatory values:
         - job_name: name of the job to start;
         - entity_name: name of the entity (hopefully with an agent
                        installed on) that should start the job;
         - offset: delay for the scheduler on the agent before starting
                   the job;
         - job_arguments: key=value pairs of arguments provided to
                          the job on the command line when starting it.
        """

        arguments = self.start_job_instance
        arguments.clear()
        arguments['entity_name'] = entity_name
        arguments['offset'] = offset
        arguments[job_name] = job_arguments
        self.job_name = job_name

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        if self.job_name is None:
            raise ImproperlyConfiguredFunction('start_job_instance')

        context = super().build(functions, function_id)

        job = self.job_name
        function = self.start_job_instance
        context['start_job_instance'] = {
            'entity_name': function['entity_name'],
            'offset': function['offset'],
            job: self._prepare_arguments(function[job], functions),
        }

        return context

    @staticmethod
    def _prepare_arguments(arguments, functions):
        if isinstance(arguments, dict):
            return {
                    key: StartJobInstance._prepare_arguments(value, functions)
                    for key, value in arguments.items()
            }
        elif isinstance(arguments, list):
            return [
                    StartJobInstance._prepare_arguments(arg, functions)
                    for arg in arguments
            ]
        elif isinstance(arguments, (StartJobInstance, StartScenarioInstance)):
            try:
                return next(safe_indexor(functions, [arguments]))
            except StopIteration:
                raise ImproperlyConfiguredFunction('start_job_instance')
        else:
            return arguments


class StopJobInstance(OpenBachFunction):
    """Representation of the stop_job_instance openbach function."""

    def __init__(self, launched, finished, delay, label):
        super().__init__(launched, finished, delay, label)
        self.openbach_function_indexes = ()

    def configure(self, *openbach_functions):
        """Define this openbach function with the mandatory values:
         - openbach_functions: list of openbach functions to stop.
        """

        if not all(isinstance(f, StartJobInstance) for f in openbach_functions):
            raise TypeError('{}.configure() arguments must '
                            'be StartScenarioInstance\'s '
                            'instances'.format(self.__class__.__name__))

        self.openbach_function_indexes = openbach_functions

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        context = super().build(functions, function_id)
        context['stop_job_instances'] = {
            'openbach_function_ids': list(
                safe_indexor(functions, self.openbach_function_indexes))}
        return context


class StartScenarioInstance(OpenBachFunction):
    """Representation of the start_scenario_instance openbach function."""

    def __init__(self, launched, finished, delay, label):
        super().__init__(launched, finished, delay, label)
        self.scenario_name = None

    def configure(self, scenario_name, **scenario_arguments):
        """Define this openbach function with the mandatory values:
         - scenario_name: name of the sub-scenario to start.
         - scenario_arguments: dictionary of arguments to use in
                               order to start the sub-scenario.
         - date: timestamp at which to start the sub-scenario.
                 [unused in OpenBach at the moment]
        """

        self.scenario_name = scenario_name
        self.scenario_arguments = scenario_arguments

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        if self.scenario_name is None:
            raise ImproperlyConfiguredFunction('start_scenario_instance')

        context = super().build(functions, function_id)
        context['start_scenario_instance'] = {
            'scenario_name': str(self.scenario_name),
            'arguments': self.scenario_arguments,
        }
        return context


class StopScenarioInstance(OpenBachFunction):
    """Representation of the stop_scenario_instance openbach functio."""

    def __init__(self, launched, finished, delay, label):
        super().__init__(launched, finished, delay, label)
        self.openbach_function_id = None

    def configure(self, openbach_function):
        """Define this openbach function with the mandatory values:
         - openbach_function: instance of the openbach function to
                              stop. This function must be a
                              StartScenarioInstance instance.
        """

        if not isinstance(openbach_function, StartScenarioInstance):
            raise TypeError('{}.configure() argument must '
                            'be a StartScenarioInstance '
                            'instance'.format(self.__class__.__name__))

        self.openbach_function_id = openbach_function

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        if self.openbach_function_id is None:
            raise ImproperlyConfiguredFunction('stop_scenario_instance')

        ids = self.openbach_function_id,
        try:
            openbach_function_id, = safe_indexor(functions, ids)
        except ValueError:
            raise ValueError('configured function in stop_scenario_instance '
                             'does not reference a valid openbach_function '
                             'for this scenario') from None

        context = super().build(functions, function_id)
        context['stop_scenario_instance'] = {
            'openbach_function_id': openbach_function_id,
        }
        return context


class _Condition(OpenBachFunction):
    """Intermediate representation for openbach function
    that makes use of conditions.
    """

    def __init__(self, launched, finished, delay, label):
        super().__init__(launched, finished, delay, label)
        self.condition = None
        self.branch_true = ()
        self.branch_false = ()

    def configure(self, condition):
        """Define this openbach function with the mandatory values:
         - condition: test to execute during the scenario execution.
        """

        if not isinstance(condition, Condition):
            raise TypeError('{}.configure() argument should be an '
                            'instance of `Condition`'.format(
                            self.__class__.__name__))

        self.condition = condition

    def _check_openbach_functions(self, functions, name):
        if not all(isinstance(f, OpenBachFunction) for f in functions):
            raise TypeError('{}.{}() arguments must be OpenBachFunction\'s '
                            'instances'.format(self.__class__.__name__, name))

    def build(self, functions, function_id, name, branch_true_name, branch_false_name):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        if self.condition is None:
            raise ImproperlyConfiguredFunction(name)

        context = super().build(functions, function_id)
        context[name] = {
            'condition': self.condition.build(functions),
            branch_true_name: list(safe_indexor(functions, self.branch_true)),
            branch_false_name: list(safe_indexor(functions, self.branch_false)),
        }
        return context


class If(_Condition):
    """Representation of the if openbach function."""

    def configure_if_true(self, *openbach_functions):
        """Define the functions to execute if the test evaluates
        to True during the scenario execution.
        """

        self._check_openbach_functions(openbach_functions, 'configure_if_true')
        self.branch_true = openbach_functions

    def configure_if_false(self, *openbach_functions):
        """Define the functions to execute if the test evaluates
        to False during the scenario execution.
        """

        self._check_openbach_functions(openbach_functions, 'configure_if_false')
        self.branch_false = openbach_functions

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        name_true = 'openbach_functions_true'
        name_false = 'openbach_functions_false'
        return super().build(functions, function_id, 'if', name_true, name_false)


class While(_Condition):
    """Representation of the while openbach function."""

    def configure_while_body(self, *openbach_functions):
        """Define the functions to execute if the test evaluates
        to True during the scenario execution.
        """

        self._check_openbach_functions(openbach_functions, 'configure_while_body')
        self.branch_true = openbach_functions

    def configure_while_end(self, *openbach_functions):
        """Define the functions to execute if the test evaluates
        to False during the scenario execution.
        """

        self._check_openbach_functions(openbach_functions, 'configure_while_end')
        self.branch_false = openbach_functions

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        name_true = 'openbach_functions_while'
        name_false = 'openbach_functions_end'
        return super().build(functions, function_id, 'while', name_true, name_false)


def safe_indexor(reference, lookup):
    """Generate the index of each element of `lookup` in the
    `reference` array.

    Skip missing elements.
    """

    for element in lookup:
        try:
            yield reference.index(element)
        except ValueError:
            pass
