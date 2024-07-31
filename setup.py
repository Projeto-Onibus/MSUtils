from setuptools import setup 


setup(name='microservice_utils',
      version='0.1',
      description='App to make client and server classes for microservice implementations',
      url='http://github.com/Projeto-Onibus',
      author='Fernando Dias',
      author_email='fernando.dias@poli.ufrj.br',
      license='MIT',
      packages=['microservice_utils'],
      install_requires=[
        'python-logging-loki',
        'pika',
        'redis'
      ],
      zip_safe=False)
