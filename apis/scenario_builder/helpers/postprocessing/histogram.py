def cdf_on_same_graph (scenario, pp_entity, jobs_to_pp, bins, statistics, label, title, wait_finished=None, wait_launched=None, wait_delay=0):

    histogram = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    histogram.configure(
            'histogram', pp_entity, offset=0,
            jobs=[jobs_to_pp],
            bins=bins,
            statistics=statistics,
            label=label,
            title=title,
            cumulative=True)

    return [histogram]

def pdf_on_same_graph (scenario, pp_entity, jobs_to_pp, bins, statistics, label, title, wait_finished=None, wait_launched=None, wait_delay=0):

    histogram = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    histogram.configure(
            'histogram', pp_entity, offset=0,
            jobs=[jobs_to_pp],
            bins=bins,
            statistics=statistics,
            label=label,
            title=title,
            cumulative=False)

    return [histogram]
