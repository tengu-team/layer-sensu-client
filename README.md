# Description
This subordinate charm works in conjunction with the [Sensu-base charm](https://github.com/tengu-team/layer-sensu-base).
It allows monitoring of any application, using all the measurement scripts [provided by Sensu](http://sensu-plugins.io/plugins/). Other measurement scripts can be provided as well, but this must be done manually.

This charm can relate to any other charm, since it uses the juju-info relation.

In normal use, this charm will be deployed multiple times to a model, with different names. This way, different sets of measurements can be passed using juju config (see [config.yaml](https://github.com/tengu-team/layer-sensu-client/blob/master/config.yaml)for extra info).

# Installation
This installation assumes you have a running instance of sensu-base and for ssl that you have your ssl-certs generated by the sensu-tool.
```
juju deploy cs:~tengu-team/sensu-client
```
The sensu-client requires 2 config options, password, which is the vhost password for the rabbitmq-server, exposed in juju status. The other one is rabbitmq, which is the privateip:port of the rabbitmq-instance. When using ssl, 2 extra config options must be set. Assuming you are in the sensu_ssl_tool directory:
```
juju config sensu-client rabbitmq="private_ip:port"
juju config sensu-client password="[rabbitmq password]"
juju config sensu-client ssl_key="`cat client/key.pem`" ssl_cert="`cat client/cert.pem`"
```
Then all that remains is (with your_service being the service that you want to monitor):
```
juju add-relation sensu-client your_service
```
No special relation is required on the service you want to monitor, it's the juju-info interface that is used.
# Monitoring plugins and script
Providing extra plugins and scripts for monitoring can be done using config values. See the description in config.yaml for extra info.

# Monitoring data
Sensu client is configured that a measurement will return the modelname, machine-number, and monitored unit (application name and unit number)

# Remarks
Only one Sensu-base is needed to monitor all the services in a controller. The sensu-client just need the private ip, port and ssl-data of the RabbitMQ. For now this is given through config options, but when cross-model relations become available, this should be rewritten using a relation.

# Bugs
Report bugs on [Github](https://github.com/Qrama/monitoring-api/issues)

# Author
Mathijs Moerman <mathijs.moerman@tengu.io>
