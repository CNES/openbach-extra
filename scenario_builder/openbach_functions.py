class ImproperlyConfiguredFunction(Exception):
    def __init__(self, name):
        super().__init__('{} has not been configured yet'.format(name))


class OpenBachFunction:
    def __init__(self, launched, finished, delay):
        self.wait = {
            'time': delay,
            'launched_indexes': launched,
            'finished_indexes': finished,
        }

    def build(self, functions):
        context = {'wait': {'time': self.wait['time']}}
        context['wait']['launched_indexes'] = list(
                safe_indexor(functions, self.wait['launched_indexes']))
        context['wait']['finished_indexes'] = list(
                safe_indexor(functions, self.wait['finished_indexes']))
        return context


class StartJobInstance(OpenBachFunction):
    def __init__(self, launched, finished, delay):
        super().__init__(launched, finished, delay)
        self.start_job_instance = {}
        self.job_name = None

    def configure(self, job_name, agent_ip, offset=0, **job_arguments):
        arguments = self.start_job_instance
        arguments.clear()
        arguments['agent_ip'] = agent_ip
        arguments['offset'] = offset
        arguments[job_name] = job_arguments
        self.job_name = job_name

    def build(self, functions):
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
    def __init__(self, launched, finished, delay):
        super().__init__(launched, finished, delay)
        self.openbach_function_indexes = ()

    def configure(self, *functions):
        self.openbach_function_indexes = functions

    def build(self, functions):
        context = super().build(functions)
        context['stop_job_instance'] = {
            'openbach_function_indexes': list(
                safe_indexor(functions, self.openbach_function_indexes))}
        return context


def safe_indexor(reference, lookup):
    for element in lookup:
        try:
            yield reference.index(element)
        except ValueError:
            pass
