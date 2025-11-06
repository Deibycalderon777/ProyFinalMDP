# config/database.py
import mysql.connector
from contextlib import contextmanager
from typing import Dict, Any, List

# Define una excepción personalizada para un manejo claro de errores
class ConnectionError(Exception):
    """Excepción levantada cuando todas las configuraciones de BD fallan."""
    pass

class DatabaseConfig:
    def __init__(self):
        # Lista de configuraciones de bases de datos, por orden de preferencia
        self.configs: List[Dict[str, Any]] = [
            # Configuración Principal (Primary)
            {
                "host": "127.0.0.1",
                "database": "netmonitor",
                "user": "administrador",
                "password": "@Skynet007"
            },
            # Configuración de Respaldo (Failover/Secondary)
            {
                # **CAMBIA ESTOS VALORES POR TU SERVIDOR DE RESPALDO REAL**
                "host": "185.232.14.52", # Ejemplo de IP de respaldo 
                "database": "u760464709_23005089_bd",
                "user": "u760464709_23005089_usr",
                "password": ":Sa[MX~2l"
            }
        ]

    @contextmanager
    def get_connection(self):
        """Context manager para manejo seguro de conexiones con failover."""
        connection = None
        last_error = None
        
        # Intenta conectar con cada configuración en orden
        for config_num, config in enumerate(self.configs):
            try:
                # Intenta crear la conexión con la configuración actual
                print(f"Intentando conectar a la BD #{config_num + 1} en host: {config['host']}...")
                connection = mysql.connector.connect(**config)
                
                # Si la conexión tiene éxito, salimos del bucle
                if connection.is_connected():
                    print(f"Conexión exitosa a la BD #{config_num + 1}.")
                    break
                
            except mysql.connector.Error as err:
                # Si la conexión falla, guarda el error y pasa a la siguiente configuración
                last_error = err
                print(f"Fallo al conectar a la BD #{config_num + 1}. Error: {err}")
                connection = None # Asegúrate de que connection sea None si falla
        
        # Si al final del bucle no hay conexión, levantamos el error
        if connection is None:
            raise ConnectionError(
                f"Todas las configuraciones de base de datos fallaron. Último error: {last_error}"
            )
            
        # Si la conexión fue exitosa, la proporcionamos al bloque 'with'
        try:
            yield connection
        
        # El bloque finally garantiza que la conexión se cierre
        finally:
            if connection and connection.is_connected():
                connection.close()
                print("Conexión a la BD cerrada.")