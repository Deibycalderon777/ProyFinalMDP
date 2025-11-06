# config/database.py
import mysql.connector
from contextlib import contextmanager

class DatabaseConfig:
    def __init__(self):
        self.config = {
            "host": "185.232.14.52",
            "database": "u760464709_23005089_bd",
            "user": "u760464709_23005089_usr",
            "password": ":Sa[MX~2l"
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager para manejo seguro de conexiones"""
        con = mysql.connector.connect(**self.config)
        try:
            if not con.is_connected():
                con.reconnect()
            yield con
        finally:
            if con.is_connected():
                con.close()