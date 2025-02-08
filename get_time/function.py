import datetime

class GetTimeFunction:
    def __init__(self, lollmsElfServer):
        self.lollmsElfServer = lollmsElfServer
        
    def run(self, **kwargs):
        """Returns the current server time in ISO format"""
        return {
            "current_time": datetime.datetime.now().isoformat(),
            "message": "Retrieved server time successfully"
        }