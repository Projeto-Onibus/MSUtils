# MSUtils
Library that implements common functionality for the Microsservices designed for FAS-Bus

The FAS-Bus architecture consists of multiple MS that interacts with eachother through RabbitMQ, a message broker.
This library will deal with the following features:
 
- Easier request/response interface through the broker
- Logger definition with grafana loki
- Some middleware functions such as:
    - Transaction UUID creation and tracking

## Usage

In the `examples` directory there are three main use cases for this library:
- `client.py`: Demonstrates how a client application can interact with the broker to do requests.
- `server.py`: Demonstrates how a server application can be built to handle requests.
- `server-on-server.py`: Demonstrates how a server application can ask requests as a client to other servers. 

