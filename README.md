# datadog-eureka-health
This repository contains Datadog check to query Eureka servers health and sample dashboard for collected metrics.

## How to install datadog custom check
* Copy checks.d/eurekahealth.py to /etc/dd-agent/conf.d/eurekahealth.py
* Configure check according to your Eureka setup (see conf.d/eurekahealth.yaml.example for reference)
* Install required python modules:
```pip install lxml pydns```
* Restart datadog agent

## License
[Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0)
