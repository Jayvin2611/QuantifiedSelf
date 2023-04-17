import json
from werkzeug.exceptions import HTTPException
from flask import make_response

class BusinessValidationError(HTTPException):
    def __init__(self, status_code, error_code, error_msg):
        message = {'error_code': error_code, 'error_message': error_msg}
        self.response = make_response(json.dumps(message), status_code, {"Content-Type": "application/json"})

class BusinessValidationSuccessful(HTTPException):
    def __init__(self):
        message = {'code': "Successful", 'message': "Request Done Successfully"}
        self.response = make_response(json.dumps(message), 200, {"Content-Type": "application/json"})