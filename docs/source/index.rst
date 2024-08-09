.. microfw documentation master file, created by
   sphinx-quickstart on Fri Aug  9 15:06:55 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

microfw documentation
=====================

The MICROserviceFrameWork is a tool to build microservices within an open-source environment that contains numerous applications for communication between microservices, caching and logging. 

The main goal is to provide with few lines of code, a scalable, robust and integrated microservice environment. For this, numerous project decisions about the inner workings of the applications were already taken to offload those decisions from the developers. Details of the 

This library implement some commom microservice architecture mechanisms, such as:

* Sync and Async calls with `RabbitMQ <https://rabbitmq.com>`_
* Global response cache with `Redis <https://redis.io>`_
* Global log aggregation with `Grafana Loki <https://grafana.com/oss/loki/>`_
* Data visualization with `Grafana <https://grafana.com>`_

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage
   api
