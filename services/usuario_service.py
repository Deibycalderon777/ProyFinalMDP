# services/usuario_service.py
from repositories.usuario_repository import UsuarioRepository
from models.usuario import Usuario
from datetime import datetime, timedelta
import re


class UsuarioService:
    def __init__(self):
        self.usuario_repository = UsuarioRepository()
        self.MAX_INTENTOS_FALLIDOS = 5
        self.TIEMPO_BLOQUEO_MINUTOS = 30

    def authenticate_user(self, username_or_email, password):
        """Autenticar usuario con credenciales (nombre o email).
        Maneja bloqueos por intentos fallidos."""
        try:
            usuario = self.usuario_repository.find_by_username_or_email(username_or_email)

            if not usuario:
                return {'success': False, 'message': 'Usuario no encontrado', 'user': None}

            # Verificar si el usuario está activo
            if not usuario.activo:
                return {'success': False, 'message': 'Usuario inactivo. Contacta al administrador', 'user': None}

            # Verificar si el usuario está bloqueado
            if usuario.bloqueado_hasta:
                if datetime.utcnow() < usuario.bloqueado_hasta:
                    tiempo_restante = (usuario.bloqueado_hasta - datetime.utcnow()).seconds // 60
                    return {
                        'success': False,
                        'message': f'Usuario bloqueado. Intenta en {tiempo_restante} minutos',
                        'user': None
                    }
                else:
                    # Desbloquear si ya pasó el tiempo
                    self.usuario_repository.desbloquear_usuario(usuario.id)
                    usuario.intentos_fallidos = 0
                    usuario.bloqueado_hasta = None

            # Verificar contraseña
            if usuario.verify_password(password):
                # Login exitoso: resetear intentos fallidos y actualizar último acceso
                self.usuario_repository.update_intentos_fallidos(usuario.id, 0)
                self.usuario_repository.update_ultimo_acceso(usuario.id)
                
                return {
                    'success': True,
                    'message': f'Bienvenido {usuario.nombre}',
                    'user': usuario.to_dict()
                }

            # Contraseña incorrecta: incrementar intentos fallidos
            intentos = (usuario.intentos_fallidos or 0) + 1
            self.usuario_repository.update_intentos_fallidos(usuario.id, intentos)

            if intentos >= self.MAX_INTENTOS_FALLIDOS:
                # Bloquear usuario
                bloqueado_hasta = datetime.utcnow() + timedelta(minutes=self.TIEMPO_BLOQUEO_MINUTOS)
                self.usuario_repository.bloquear_usuario(usuario.id, bloqueado_hasta)
                return {
                    'success': False,
                    'message': f'Usuario bloqueado por {self.TIEMPO_BLOQUEO_MINUTOS} minutos debido a múltiples intentos fallidos',
                    'user': None
                }

            intentos_restantes = self.MAX_INTENTOS_FALLIDOS - intentos
            return {
                'success': False,
                'message': f'Contraseña incorrecta. {intentos_restantes} intentos restantes',
                'user': None
            }

        except Exception as e:
            return {'success': False, 'message': f'Error en la autenticación: {str(e)}', 'user': None}

    def get_user_by_id(self, user_id):
        """Obtener usuario por ID"""
        try:
            usuario = self.usuario_repository.find_by_id(user_id)
            if usuario:
                return {'success': True, 'user': usuario.to_dict()}
            return {'success': False, 'message': 'Usuario no encontrado'}
        except Exception as e:
            return {'success': False, 'message': f'Error al obtener usuario: {str(e)}'}

    def create_user(self, nombre, email, plain_password, rol_id: int = None):
        """Crear nuevo usuario. Hashea la contraseña y genera uuid."""
        try:
            # Validaciones
            validacion = self._validar_datos_usuario(nombre, email, plain_password)
            if not validacion['valid']:
                return {'success': False, 'message': validacion['message']}

            # Verificar si el nombre o email ya existen
            existing_user = self.usuario_repository.find_by_username_or_email(nombre)
            if existing_user:
                return {'success': False, 'message': 'El nombre de usuario ya existe'}

            existing_email = self.usuario_repository.find_by_username_or_email(email)
            if existing_email:
                return {'success': False, 'message': 'El email ya está registrado'}

            # Si no se especifica rol, asignar rol de usuario normal (2)
            if rol_id is None:
                rol_id = 2

            nuevo_usuario = Usuario.new_from_plain_password(nombre, email, plain_password, rol_id)
            user_id = self.usuario_repository.create_user(nuevo_usuario)

            return {'success': True, 'message': 'Usuario creado exitosamente', 'user_id': user_id}

        except Exception as e:
            return {'success': False, 'message': f'Error al crear usuario: {str(e)}'}
            
    def get_all_users(self):
        """Obtener lista de todos los usuarios"""
        try:
            users = self.usuario_repository.get_all_users()
            return {
                'success': True,
                'users': [user.to_dict() for user in users],
                'count': len(users)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al obtener usuarios: {str(e)}'
            }
            
    def update_user(self, user_id: int, data: dict):
        """Actualizar datos de usuario"""
        try:
            # Verificar si el usuario existe
            user = self.usuario_repository.find_by_id(user_id)
            if not user:
                return {'success': False, 'message': 'Usuario no encontrado'}

            # Preparar datos para actualización
            update_data = {}

            # Si se va a actualizar contraseña, validarla y hashearla
            if 'password' in data and data['password']:
                validacion = self._validar_contrasena(data['password'])
                if not validacion['valid']:
                    return {'success': False, 'message': validacion['message']}
                update_data['password_hash'] = Usuario.hash_password(data['password'])
                
            # Si se intenta cambiar nombre, verificar que no exista
            if 'nombre' in data and data['nombre'] != user.nombre:
                validacion = self._validar_nombre(data['nombre'])
                if not validacion['valid']:
                    return {'success': False, 'message': validacion['message']}
                    
                existing = self.usuario_repository.find_by_username_or_email(data['nombre'])
                if existing and existing.id != user_id:
                    return {'success': False, 'message': 'El nombre de usuario ya existe'}
                update_data['nombre'] = data['nombre']
                    
            # Si se intenta cambiar email, verificar que no exista
            if 'email' in data and data['email'] != user.email:
                validacion = self._validar_email(data['email'])
                if not validacion['valid']:
                    return {'success': False, 'message': validacion['message']}
                    
                existing = self.usuario_repository.find_by_username_or_email(data['email'])
                if existing and existing.id != user_id:
                    return {'success': False, 'message': 'El email ya está registrado'}
                update_data['email'] = data['email']

            # Actualizar rol si se proporciona
            if 'rol_id' in data:
                update_data['rol_id'] = int(data['rol_id'])

            # Actualizar estado activo si se proporciona
            if 'activo' in data:
                update_data['activo'] = 1 if data['activo'] else 0

            # Si no hay nada que actualizar
            if not update_data:
                return {'success': False, 'message': 'No hay datos para actualizar'}
            
            # Intentar actualizar
            updated = self.usuario_repository.update_user(user_id, update_data)
            if updated:
                return {
                    'success': True,
                    'message': 'Usuario actualizado correctamente'
                }
            return {
                'success': False,
                'message': 'No se pudo actualizar el usuario'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al actualizar usuario: {str(e)}'
            }
            
    def delete_user(self, user_id: int):
        """Eliminar usuario por ID"""
        try:
            # Verificar si existe
            user = self.usuario_repository.find_by_id(user_id)
            if not user:
                return {'success': False, 'message': 'Usuario no encontrado'}

            # Prevenir eliminar el último administrador
            if user.rol_id == 1:
                users = self.usuario_repository.search_users(rol_id=1)
                if len(users) <= 1:
                    return {
                        'success': False,
                        'message': 'No se puede eliminar el último administrador del sistema'
                    }
                
            # Intentar eliminar
            deleted = self.usuario_repository.delete_user(user_id)
            if deleted:
                return {
                    'success': True,
                    'message': 'Usuario eliminado correctamente'
                }
            return {
                'success': False,
                'message': 'No se pudo eliminar el usuario'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al eliminar usuario: {str(e)}'
            }

    def search_users(self, search_term: str = None, rol_id: int = None, activo: bool = None):
        """Buscar usuarios con filtros opcionales"""
        try:
            users = self.usuario_repository.search_users(search_term, rol_id, activo)
            return {
                'success': True,
                'users': [user.to_dict() for user in users],
                'count': len(users)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al buscar usuarios: {str(e)}'
            }

    def toggle_user_status(self, user_id: int):
        """Activar o desactivar un usuario"""
        try:
            user = self.usuario_repository.find_by_id(user_id)
            if not user:
                return {'success': False, 'message': 'Usuario no encontrado'}

            nuevo_estado = self.usuario_repository.toggle_activo(user_id)
            
            if nuevo_estado is not None:
                estado_texto = 'activado' if nuevo_estado else 'desactivado'
                return {
                    'success': True,
                    'message': f'Usuario {estado_texto} correctamente',
                    'activo': nuevo_estado
                }
            return {'success': False, 'message': 'No se pudo cambiar el estado del usuario'}
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al cambiar estado: {str(e)}'
            }

    def unlock_user(self, user_id: int):
        """Desbloquear un usuario manualmente"""
        try:
            user = self.usuario_repository.find_by_id(user_id)
            if not user:
                return {'success': False, 'message': 'Usuario no encontrado'}

            self.usuario_repository.desbloquear_usuario(user_id)
            return {
                'success': True,
                'message': 'Usuario desbloqueado correctamente'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al desbloquear usuario: {str(e)}'
            }

    # Métodos de validación privados
    def _validar_datos_usuario(self, nombre, email, password):
        """Validar todos los datos de un nuevo usuario"""
        val_nombre = self._validar_nombre(nombre)
        if not val_nombre['valid']:
            return val_nombre

        val_email = self._validar_email(email)
        if not val_email['valid']:
            return val_email

        val_password = self._validar_contrasena(password)
        if not val_password['valid']:
            return val_password

        return {'valid': True}

    def _validar_nombre(self, nombre):
        """Validar nombre de usuario"""
        if not nombre or len(nombre.strip()) < 3:
            return {'valid': False, 'message': 'El nombre debe tener al menos 3 caracteres'}
        if len(nombre) > 50:
            return {'valid': False, 'message': 'El nombre no puede exceder 50 caracteres'}
        if not re.match(r'^[a-zA-Z0-9_]+$', nombre):
            return {'valid': False, 'message': 'El nombre solo puede contener letras, números y guiones bajos'}
        return {'valid': True}

    def _validar_email(self, email):
        """Validar formato de email"""
        if not email or len(email.strip()) < 5:
            return {'valid': False, 'message': 'Email inválido'}
        if len(email) > 150:
            return {'valid': False, 'message': 'El email es demasiado largo'}
        # Regex básico para email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return {'valid': False, 'message': 'Formato de email inválido'}
        return {'valid': True}

    def _validar_contrasena(self, password):
        """Validar contraseña (mínimo 6 caracteres)"""
        if not password or len(password) < 6:
            return {'valid': False, 'message': 'La contraseña debe tener al menos 6 caracteres'}
        if len(password) > 100:
            return {'valid': False, 'message': 'La contraseña es demasiado larga'}
        return {'valid': True}