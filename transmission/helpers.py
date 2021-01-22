from datetime import datetime
from .models import APIError

def log_api_error(error, endpoint, log_time=datetime.now()):
    print('logging')
    error = APIError(error=error, endpoint=endpoint, log_time=log_time)
    error.save()