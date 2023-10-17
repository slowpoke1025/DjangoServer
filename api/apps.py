from django.apps import AppConfig

from api.utils.ethereum import setup_web3


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        print("------------ ready ----------")
        setup_web3()
