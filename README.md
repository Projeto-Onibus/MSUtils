# MSUtils
Library that implements common functionality for the Microsservices designed for FAS-Bus

The FAS-Bus architecture consists of multiple MS that interacts with eachother through RabbitMQ, a message broker.
This library will deal with the following features:
 
- Easier request/response interface through the broker
- Logger definition with grafana loki
- Some middleware functions such as:
    - Transaction UUID creation and tracking

## Current roadmap

There's a decorator and a channel initializer to ease server-side code's development. 
Next step is to create a library for client-side. This 

The logger will be defined with python-logging-loki.
