# MSUtils
Library that implements common functionality for the Microsservices designed for FAS-Bus

The FAS-Bus architecture consists of multiple MS that interacts with eachother through RabbitMQ, a message broker.
This library will deal with the following features:
 
- Easier request/response interface through the broker
- Logger definition with grafana loki
- Some middleware functions such as:
    - Transaction UUID creation and tracking

## Testing

To test this application, first install the package locally by running on the root of this repository

```
python3 -m pip install .
```

After, go to `tests` and raise the conteiners in the compose files. This can be done using:

```
docker compose up -d
```

After this, initiate in the background the `example-server-*.py` microservices and do a request using `example-client.py`.

## Roadmap 

- [ ] (Bugfix) positive status-code passing through the MakeCall command
- [ ] Have a way to query transaction ids in grafana
- [ ] Pass the global counter with the transaction_ids
- [ ] Add schema validation to services

