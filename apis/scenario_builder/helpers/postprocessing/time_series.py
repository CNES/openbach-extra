def time_series_on_same_graph (scenario, pp_entity, jobs_to_pp, statistics, label, title, wait_finished=None, wait_launched=None, wait_delay=0):

    time_series = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    time_series.configure(
            'time_series', pp_entity, offset=0,
            jobs=[jobs_to_pp],
            statistics=statistics,
            label=label,
            title=title)

    return [time_series]
