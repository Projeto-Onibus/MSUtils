
class AppException(BaseException):
    def __init__(self,statusCode,message):
        self.statusCode = statusCode
        self.message = message
        pass

class ClientException(AppException):
    def __init__(self,message):
        self.statusCode=400
        self.message = message

class ServerException(AppException):
    def __init__(self,message):
        self.statusCode=500
        self.message = message
