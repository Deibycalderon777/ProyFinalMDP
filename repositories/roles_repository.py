from config.database import DatabaseConfig, ConnectionError # Importamos tu clase
from typing import List, Dict, Any, Optional

class RolesRepository:
    """Clase para operaciones CRUD directas en la tabla 'roles'."""
    def __init__(self):
        # Inicializa la configuración de la BD
        self.db_config = DatabaseConfig()

    def _execute_query(self, query: str, params: tuple = None, fetch_one: bool = False) -> Optional[List[Dict[str, Any]]]:
        """Método helper para ejecutar consultas de lectura y devolver resultados."""
        result = None
        try:
            # Usamos el context manager para obtener y cerrar la conexión automáticamente
            with self.db_config.get_connection() as conn:
                # Nota: Asume que conn.cursor(dictionary=True) funciona para tu motor de BD
                cursor = conn.cursor(dictionary=True) 
                cursor.execute(query, params)
                
                if query.strip().upper().startswith(("SELECT")):
                    result = cursor.fetchone() if fetch_one else cursor.fetchall()
                
                cursor.close()
                
        except ConnectionError as e:
            # Re-lanzar el error de conexión para que el Service lo maneje
            raise e
        except Exception as e:
            print(f"Error en la consulta de lectura: {e}")
            return None 

        return result


    def _execute_commit(self, query: str, params: tuple = None) -> bool:
        """Método helper para ejecutar consultas de escritura (INSERT, UPDATE)."""
        # IMPORTANTE: Este método retorna True/False solo si el commit tuvo éxito, 
        # pero no revisa si se afectó alguna fila. Esto es aceptable para INSERT,
        # pero DELETE y UPDATE suelen requerir el chequeo de rowcount.
        try:
            with self.db_config.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit() # ¡Importante! Confirmar los cambios
                cursor.close()
                return True
        except ConnectionError as e:
            raise e
        except Exception as e:
            print(f"Error en la consulta de escritura: {e}")
            return False

    # --- Métodos de la tabla 'roles' ---
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Obtiene todos los roles."""
        query = "SELECT id, nombre, descripcion, created_at FROM roles"
        return self._execute_query(query) or []

    def get_by_id(self, role_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un rol por su ID."""
        query = "SELECT id, nombre, descripcion, created_at FROM roles WHERE id = %s"
        return self._execute_query(query, (role_id,), fetch_one=True)

    def create(self, nombre: str, descripcion: str) -> bool:
        """Crea un nuevo rol. Usamos NOW() para created_at."""
        query = "INSERT INTO roles (nombre, descripcion, created_at) VALUES (%s, %s, NOW())"
        return self._execute_commit(query, (nombre, descripcion))

    def update(self, role_id: int, nombre: Optional[str] = None, descripcion: Optional[str] = None) -> bool:
        """Actualiza un rol existente."""
        updates = []
        params = []
        if nombre is not None:
            updates.append("nombre = %s")
            params.append(nombre)
        if descripcion is not None:
            updates.append("descripcion = %s")
            params.append(descripcion)
            
        if not updates:
            return False 

        query = "UPDATE roles SET " + ", ".join(updates) + " WHERE id = %s"
        params.append(role_id)
        
        # NOTE: Aquí _execute_commit devuelve True aunque no se encuentre el ID. 
        # Pero el Service ya valida la existencia.
        return self._execute_commit(query, tuple(params))

    def delete(self, role_id: int) -> bool:
        """
        [FIXED] Elimina un rol por su ID y verifica si una fila fue afectada.
        """
        query = "DELETE FROM roles WHERE id = %s"

        try:
            # Manejamos la conexión aquí para poder acceder al rowcount
            with self.db_config.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (role_id,))
                
                # CRÍTICO: Comprobar el número de filas eliminadas
                rows_affected = cursor.rowcount
                conn.commit() 
                cursor.close()
                
                # Si rows_affected es mayor que 0, la eliminación fue exitosa
                if rows_affected > 0:
                    return True
                else:
                    # Retorna False si el rol no existía o no se pudo borrar
                    return False
                    
        except ConnectionError as e:
            # Re-lanzar el error de conexión
            raise e
        except Exception as e:
            print(f"Error en la consulta de eliminación: {e}")
            # La conexión se cerrará automáticamente, pero marcamos fallo
            return False