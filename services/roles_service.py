from repositories.roles_repository import RolesRepository
from typing import List, Dict, Any, Optional

class RolesService:
    """
    Clase que maneja la lógica de negocio para Roles, utilizando el Repositorio
    para la persistencia de datos. Ahora incluye manejo básico de errores de BD.
    """
    
    def __init__(self):
        # Inyectamos el Repositorio como dependencia
        # El Repositorio es la capa que se comunica directamente con la BD (sqlite3)
        self.repository = RolesRepository()

    def obtener_todos(self):
        """Retorna todos los roles en el formato de respuesta esperado, consultando a la BD."""
        try:
            # Llama al método get_all() del Repositorio (Acceso a BD real)
            roles = self.repository.get_all()
            return {
                "success": True, 
                "data": roles,
                "message": "Roles obtenidos exitosamente"
            }
        except Exception as e: 
            # Captura errores de conexión o de consulta del Repositorio
            print(f"Error al obtener roles: {e}")
            return {
                "success": False, 
                "data": [],
                "message": "Error interno del servidor al acceder a la lista de roles.",
                "status": 500
            }


    def obtener_por_id(self, role_id):
        """Retorna un rol por su ID, o un error si no existe, consultando a la BD."""
        try:
            # Llama al método get_by_id() del Repositorio (Acceso a BD real)
            role = self.repository.get_by_id(role_id)
            if role:
                return {
                    "success": True, 
                    "data": role,
                    "message": f"Rol {role_id} obtenido"
                }
            else:
                return {
                    "success": False, 
                    "message": f"Rol {role_id} no encontrado",
                    "status": 404 # Estado HTTP en caso de error
                }
        except Exception as e:
            print(f"Error al obtener rol por ID: {e}")
            return {
                "success": False, 
                "message": "Error interno del servidor al acceder al rol.",
                "status": 500
            }

    def crear_rol(self, nombre, descripcion):
        """
        Crea un nuevo rol, delegando la persistencia al Repositorio.
        """
        # Lógica de Negocio/Validación (requiere nombre)
        if not nombre:
            return {
                "success": False, 
                "message": "El nombre del rol es obligatorio",
                "status": 400 # Bad Request
            }
        
        try:
            # Llama al método create() del Repositorio (Acceso a BD real)
            success = self.repository.create(nombre, descripcion)
            
            if success:
                # CRÍTICO: El front-end debe recargar la lista para obtener el ID real de la BD.
                return {
                    "success": True, 
                    "data": None, 
                    "message": "Rol creado exitosamente. Recargando la lista..."
                }
            else:
                 return {
                    "success": False, 
                    "message": "Fallo al insertar el rol en la base de datos (commit fallido).",
                    "status": 500
                }

        except Exception as e:
            print(f"Error al crear rol: {e}")
            return {
                "success": False, 
                "message": "Error interno del servidor al intentar crear el rol.",
                "status": 500
            }
            
    def actualizar_rol(self, role_id, nombre, descripcion):
        """
        Actualiza un rol existente, delegando la persistencia al Repositorio.
        """
        # 1. Validación de existencia (consulta a BD)
        if not self.repository.get_by_id(role_id):
            return {
                "success": False, 
                "message": f"Rol {role_id} no encontrado para actualizar.",
                "status": 404
            }
        
        # 2. Validación de datos de entrada (requiere nombre)
        if not nombre:
            return {
                "success": False, 
                "message": "El nombre del rol es obligatorio para la actualización.",
                "status": 400 # Bad Request
            }

        try:
            # Llama al método update() del Repositorio (Acceso a BD real)
            success = self.repository.update(role_id, nombre, descripcion)
            
            if success:
                return {
                    "success": True, 
                    "message": f"Rol {role_id} actualizado exitosamente."
                }
            else:
                 return {
                    "success": False, 
                    "message": "Fallo al actualizar el rol en la base de datos (commit fallido).",
                    "status": 500
                }

        except Exception as e:
            print(f"Error al actualizar rol: {e}")
            return {
                "success": False, 
                "message": "Error interno del servidor al intentar actualizar el rol.",
                "status": 500
            }

    def eliminar_rol(self, role_id):
        """
        Elimina un rol por ID, delegando la persistencia al Repositorio.
        """
        # 1. Validación de existencia (consulta a BD)
        if not self.repository.get_by_id(role_id):
            return {
                "success": False, 
                "message": f"Rol {role_id} no encontrado para eliminar.",
                "status": 404
            }

        try:
            # Llama al método delete() del Repositorio (Acceso a BD real)
            success = self.repository.delete(role_id)
            
            if success:
                return {
                    "success": True, 
                    "message": f"Rol {role_id} eliminado exitosamente."
                }
            else:
                 return {
                    "success": False, 
                    "message": "Fallo al eliminar el rol de la base de datos (commit fallido).",
                    "status": 500
                }

        except Exception as e:
            print(f"Error al eliminar rol: {e}")
            return {
                "success": False, 
                "message": "Error interno del servidor al intentar eliminar el rol.",
                "status": 500
            }