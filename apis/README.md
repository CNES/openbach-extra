OpenBACH API
============

Content
-------

 * Scenario builder: build JSON of Scenarios programmatically
 * Data access: ease retrieval of data from Collector (ElasticSearch & InfluxDB)


Scenario Builder
----------------

This package aims at easily creating definition files for Scenarios without having
to edit JSON files manually. A Scenario object can be configured with several
openbach functions; dependencies are managed using Python objects; and the scenario
can then be written to a file.

Data Access
-----------

This package ease API calls to InfluxDB and ElasticSearch and allow one to retrieve
data associated to scenarios of interest into simple Python objects.
