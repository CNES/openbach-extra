from .. import Scenario
from ..helpers.opensand import (
        OPENSAND_RUN, PLATFORM,
        build_opensand_scenario,
        configure_entities,
        reset_entities,
        WorkstationAction,
)


def build_configure_scenario(topology, name='*** BUILT *** Configure OpenSAND platform'):
    scenario_configure = Scenario(name, '')
    build_opensand_scenario(scenario_configure, topology, configure_entities, WorkstationAction.ADD)
    return scenario_configure


def build_reset_scenario(topology, name='*** BUILT *** Reset OpenSAND platform'):
    scenario_reset = Scenario(name, '')
    build_opensand_scenario(scenario_reset, topology, reset_entities, WorkstationAction.DELETE)
    return scenario_reset


def build_emulation_scenario(topology, name='*** BUILT *** Run OpenSAND Emulation'):
    scenario = Scenario(name, '')
    scenario.add_argument('opensand_scenario', 'The path to the OpenSAND scenario')

    function = scenario.add_function('start_job_instance')
    function.configure(
            'opensand_run', topology[OPENSAND_RUN], offset=0,
            **{
                'platform-id': topology[PLATFORM],
                'scenario-path': '$opensand_scenario',
            })

    return scenario
