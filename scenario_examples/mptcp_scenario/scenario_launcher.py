#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import argparse

from start_scenario_instance import StartScenarioInstance
from status_scenario_instance import StatusScenarioInstance

def main(name, project, login):
    # Start scenario instance
    start = StartScenarioInstance()
    start.parse(['--login', login, '--project', project, name])
    response = start.execute()
    try:
        scenario_id = response.json()['scenario_instance_id']
    except KeyError:
        print(response.json())
        exit(1)
    except ValueError:
        print(response.text)
        exit(1)

    # Get scenario status
    status_scenario = StatusScenarioInstance()
    status_scenario.session = start.session
    status_scenario.parse([str(scenario_id)])
    # Wait for scenario to finish
    while True:
        time.sleep(10)
        req_status = status_scenario.execute(False)
        status = req_status.json()['status']
        print("Status: {}".format(status))
        if status in {"Finished KO"}:
            return
        if status in {"Stopped", "Finished OK"}:
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('name', type=str, help='The name of the scenario')
    parser.add_argument('project', type=str, help='The name of the project')
    parser.add_argument('login', type=str, help='The login username')
    
    args = parser.parse_args()
    
    main(args.name, args.project, args.login)
