from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios.adaptive_transport import build, TrafficType

"""This script launches the *adataptive_transport* scenario from /openbach-extra/apis/scenario_builder/scenarios/ """


# Set traffic type. Accepted values: TrafficType.DASH, TrafficType.WEB_BROWSING, 
# TrafficType.MIX
TRAFFIC_TYPE = TrafficType.WEB_BROWSING

def desired_test(traffic_type, loss, congestion, cc_web_browsing, cc_dash, initcwnd):
    if traffic_type is TrafficType.MIX:
       if (congestion, cc_web_browsing, cc_dash) not in [('cubic', 'cubic', 'cubic'), ('ledbat', 'bbr2', 'bbr2'), ('ledbat', 'cubic', 'bbr2')]:
          return False

    return True

def main(scenario_name='{} tests under various network conditions'.format(TRAFFIC_TYPE.value)):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--entity_pp', help='The entity name where the post-processing will be performed')
       
    args = observer.parse(default_scenario_name=scenario_name)
    # Init network conditions are specified via two parameters,
    # 1. losses (expressed in %. eg. losses = (0.0, 1.0)) and 
    # 2. congestions. Accepted values must be a tuple of: None, 'cubic', 'bbr', 'ledbat'. 
    # eg. congestions = (None, 'cubic'))
    # A network condition corresponds to a combination of both loss and congestion.
    # Set of network conditions equals to product between losses and congestions  
    losses = (0.0, 1.0)
    congestions = (None, 'cubic')
    
    # Init tcp configurations are specified using following three parameters: 
    # 1. ccs_web_browsing: congestion controls for web_browsing
    # eg. ccs_web_browsing = ('cubic', 'bbr') 
    # 2. ccs_dash: congestion controls for dash
    # eg. ccs_dash = ('cubic',) 
    # 3. inicwnds: initial congestion windowns. eg. = (10, 30))
    # A tcp configuration corresponds to a combination of ccs and initcwnd.
    # Set of tcp configurations equals to product between ccs and initcwnds  
    ccs_web_browsing = ('cubic', 'bbr2')
    ccs_dash = ('cubic', 'bbr2')
    initcwnds = (10, 30)

    # Finally the set of tests equals to product between the network conditions and tcp configurations
    # If you don't want to run all tests, you must specify a filter function that will be use to execute only desired tests. 

    # Build scenario
    scenario = build(
                   scenario_name,
                   args.entity_pp, 
                   TRAFFIC_TYPE,
                   desired_test,
                   losses=losses,
                   congestions=congestions,
                   ccs_web_browsing=ccs_web_browsing,
                   ccs_dash=ccs_dash,
                   initcwnds=initcwnds
                   )
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
