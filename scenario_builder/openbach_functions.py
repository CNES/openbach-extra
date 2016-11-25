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

    def __init__(self, launched, finished, delay):
        self.time = delay
        self.wait_launched = launched
        self.wait_finished = finished

    def build(self, functions):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        context = {'wait': {'time': self.time}}
        context['wait']['launched_indexes'] = list(safe_indexor(functions, self.wait_launched))
        context['wait']['finished_indexes'] = list(safe_indexor(functions, self.wait_finished))
        return context


class StartJobInstance(OpenBachFunction):
    """Representation of the start_job_instance openbach function."""

    def __init__(self, launched, finished, delay):
        super().__init__(launched, finished, delay)
        self.start_job_instance = {}
        self.job_name = None

    def configure(self, job_name, agent_ip, offset=0, **job_arguments):
        """Define this openbach function with the mandatory values:
         - job_name: name of the job to start;
         - agent_ip: address of the agent that should start the job;
         - offset: delay for the scheduler on the agent before starting
                   the job;
         - job_arguments: key=value pairs of arguments provided to
                          the job on the command line when starting it.
        """

        arguments = self.start_job_instance
        arguments.clear()
        arguments['agent_ip'] = agent_ip
        arguments['offset'] = offset
        arguments[job_name] = job_arguments
        self.job_name = job_name

    def build(self, functions):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        if self.job_name is None:
            raise ImproperlyConfiguredFunction('start_job_instance')

        context = super().build(functions)

        job = self.job_name
        function = self.start_job_instance
        context['start_job_instance'] = {
            'agent_ip': function['agent_ip'],
            'offset': function['offset'],
            job: function[job].copy()
        }

        return context


class StopJobInstance(OpenBachFunction):
    """Representation of the stop_job_instance openbach function."""

    def __init__(self, launched, finished, delay):
        super().__init__(launched, finished, delay)
        self.openbach_function_indexes = ()

    def configure(self, *functions):
        """Define this openbach function with the mandatory values:
         - functions: openbach functions to stop.
        """

        self.openbach_function_indexes = functions

    def build(self, functions):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        context = super().build(functions)
        context['stop_job_instance'] = {
            'openbach_function_indexes': list(
                safe_indexor(functions, self.openbach_function_indexes))}
        return context


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
