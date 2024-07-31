#
# RPCCache - Class to implement global cache configuration
# Author: Fernando Dias 
# 
# Description: 
#   Class that implements a rudimentary caching system using redis as storage
#


import json

import redis

class RPCCache:
    def __init__(self,host,port):
        self.cache = redis.Redis(host=host,port=port)

    def SetResult(self, functionName, parameters, data):
        self.cache.set(f'{functionName},{json.dumps(parameters)}',json.dumps(data))

    def GetResult(self, functionName, parameters):
        self.cache.get(f'{functionName},{json.dumps(parameters)}')
