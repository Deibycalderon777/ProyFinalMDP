# repositories/usuario_repository.py
from config.database import DatabaseConfig
from models.usuario import Usuario
from datetime import datetime


class UsuarioRepository:
    def __init__(self):
        self.db_config = DatabaseConfig()

    def find_by_username_or_email(self, username_or_email):
        """Buscar usuario por nombre o email en la tabla users"""
        with self.db_config.get_connection() as con:
            cursor = con.cursor(dictionary=True)
            query = (
                "SELECT id, uuid, nombre, email, password_hash, rol_id, activo, "
                "ultimo_acceso, intentos_fallidos, bloqueado_hasta, created_at, updated_at "
                "FROM users WHERE nombre = %s OR email = %s"
            )
            cursor.execute(query, (username_or_email, username_or_email))
            result = cursor.fetchone()
            cursor.close()

            if result:
                return Usuario.from_dict(result)
            return None

    def find_by_id(self, user_id):
        """Buscar usuario por ID"""
        with self.db_config.get_connection() as con:
            cursor = con.cursor(dictionary=True)
            query = (
                "SELECT id, uuid, nombre, email, password_hash, rol_id, activo, "
                "ultimo_acceso, intentos_fallidos, bloqueado_hasta, created_at, updated_at "
                "FROM users WHERE id = %s"
            )
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            cursor.close()

            if result:
                return Usuario.from_dict(result)
            return None

    def create_user(self, usuario: Usuario):
        """Crear nuevo usuario en la tabla users. Espera una instancia Usuario con uuid y password_hash ya seteados."""
        with self.db_config.get_connection() as con:
            cursor = con.cursor()
            query = (
                "INSERT INTO users (uuid, nombre, email, password_hash, rol_id, activo, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            )
            cursor.execute(query, (
                usuario.uuid,
                usuario.nombre,
                usuario.email,
                usuario.password_hash,
                usuario.rol_id,
                usuario.activo,
                usuario.created_at,
                usuario.updated_at
            ))
            con.commit()
            user_id = cursor.lastrowid
            cursor.close()
            return user_id

    def get_all_users(self):
        """Obtener todos los usuarios (resumen)"""
        with self.db_config.get_connection() as con:
            cursor = con.cursor(dictionary=True)
            query = (
                "SELECT id, uuid, nombre, email, rol_id, activo, "
                "created_at, updated_at FROM users ORDER BY created_at DESC"
            )
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            return [Usuario.from_dict(row) for row in results]

    def update_user(self, user_id: int, data: dict):
        """Actualizar campos específicos de un usuario.
        
        Args:
            user_id: ID del usuario a actualizar
            data: Diccionario con los campos a actualizar (nombre, email, password_hash, rol_id, activo)
        
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        if not data:
            return False

        # Construir la query dinámicamente según los campos recibidos
        campos_permitidos = ['nombre', 'email', 'password_hash', 'rol_id', 'activo']
        campos_actualizar = []
        valores = []

        for campo in campos_permitidos:
            if campo in data:
                campos_actualizar.append(f"{campo} = %s")
                valores.append(data[campo])

        if not campos_actualizar:
            return False

        # Siempre actualizar el timestamp
        campos_actualizar.append("updated_at = %s")
        valores.append(datetime.utcnow())
        valores.append(user_id)

        query = f"UPDATE users SET {', '.join(campos_actualizar)} WHERE id = %s"

        with self.db_config.get_connection() as con:
            cursor = con.cursor()
            try:
                cursor.execute(query, tuple(valores))
                con.commit()
                affected_rows = cursor.rowcount
                cursor.close()
                return affected_rows > 0
            except Exception as e:
                con.rollback()
                cursor.close()
                raise e

    def delete_user(self, user_id: int):
        """Eliminar usuario por ID (eliminación física).
        
        Args:
            user_id: ID del usuario a eliminar
        
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        with self.db_config.get_connection() as con:
            cursor = con.cursor()
            try:
                query = "DELETE FROM users WHERE id = %s"
                cursor.execute(query, (user_id,))
                con.commit()
                affected_rows = cursor.rowcount
                cursor.close()
                return affected_rows > 0
            except Exception as e:
                con.rollback()
                cursor.close()
                raise e

    def search_users(self, search_term: str = None, rol_id: int = None, activo: bool = None):
        """Buscar usuarios con filtros opcionales.
        
        Args:
            search_term: Término de búsqueda (busca en nombre y email)
            rol_id: Filtrar por rol
            activo: Filtrar por estado activo/inactivo
        
        Returns:
            list: Lista de objetos Usuario que coinciden con los filtros
        """
        query = (
            "SELECT id, uuid, nombre, email, rol_id, activo, "
            "ultimo_acceso, created_at, updated_at FROM users WHERE 1=1"
        )
        params = []

        if search_term:
            query += " AND (nombre LIKE %s OR email LIKE %s)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])

        if rol_id is not None:
            query += " AND rol_id = %s"
            params.append(rol_id)

        if activo is not None:
            query += " AND activo = %s"
            params.append(1 if activo else 0)

        query += " ORDER BY created_at DESC"

        with self.db_config.get_connection() as con:
            cursor = con.cursor(dictionary=True)
            cursor.execute(query, tuple(params))
            results = cursor.fetchall()
            cursor.close()

            return [Usuario.from_dict(row) for row in results]

    def update_ultimo_acceso(self, user_id: int):
        """Actualizar la fecha y hora del último acceso del usuario."""
        with self.db_config.get_connection() as con:
            cursor = con.cursor()
            query = "UPDATE users SET ultimo_acceso = %s WHERE id = %s"
            cursor.execute(query, (datetime.utcnow(), user_id))
            con.commit()
            cursor.close()

    def update_intentos_fallidos(self, user_id: int, intentos: int):
        """Actualizar el contador de intentos fallidos de login."""
        with self.db_config.get_connection() as con:
            cursor = con.cursor()
            query = "UPDATE users SET intentos_fallidos = %s WHERE id = %s"
            cursor.execute(query, (intentos, user_id))
            con.commit()
            cursor.close()

    def bloquear_usuario(self, user_id: int, bloqueado_hasta: datetime):
        """Bloquear usuario hasta una fecha específica."""
        with self.db_config.get_connection() as con:
            cursor = con.cursor()
            query = "UPDATE users SET bloqueado_hasta = %s WHERE id = %s"
            cursor.execute(query, (bloqueado_hasta, user_id))
            con.commit()
            cursor.close()

    def desbloquear_usuario(self, user_id: int):
        """Desbloquear usuario (establecer bloqueado_hasta a NULL)."""
        with self.db_config.get_connection() as con:
            cursor = con.cursor()
            query = "UPDATE users SET bloqueado_hasta = NULL, intentos_fallidos = 0 WHERE id = %s"
            cursor.execute(query, (user_id,))
            con.commit()
            cursor.close()

    def toggle_activo(self, user_id: int):
        """Alternar el estado activo/inactivo de un usuario.
        
        Returns:
            bool: Nuevo estado (True = activo, False = inactivo)
        """
        with self.db_config.get_connection() as con:
            cursor = con.cursor(dictionary=True)
            
            # Obtener estado actual
            query = "SELECT activo FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                return None
            
            nuevo_estado = 0 if result['activo'] else 1
            
            # Actualizar estado
            query = "UPDATE users SET activo = %s, updated_at = %s WHERE id = %s"
            cursor.execute(query, (nuevo_estado, datetime.utcnow(), user_id))
            con.commit()
            cursor.close()
            
            return bool(nuevo_estado)