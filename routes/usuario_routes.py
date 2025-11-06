# routes/usuario_routes.py
from flask import Blueprint, request, jsonify, session
from services.usuario_service import UsuarioService

usuario_bp = Blueprint('usuario', __name__)
usuario_service = UsuarioService()

@usuario_bp.route('/api/login', methods=['POST'])
def login():
    """Endpoint para autenticación de usuarios"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos'
            }), 400
        
        username_or_email = data.get('usuario')
        password = data.get('contrasena')
        
        if not username_or_email or not password:
            return jsonify({
                'success': False,
                'message': 'Usuario y contraseña son requeridos'
            }), 400
        
        # Autenticar usuario
        result = usuario_service.authenticate_user(username_or_email, password)
        
        if result['success']:
            # Guardar información del usuario en la sesión
            session['user_id'] = result['user']['id']
            session['username'] = result['user'].get('username') or result['user'].get('nombre')
            session['rol_id'] = result['user'].get('rol_id')
            session['logged_in'] = True
            
            return jsonify(result), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error interno del servidor: {str(e)}'
        }), 500

@usuario_bp.route('/api/logout', methods=['POST'])
def logout():
    """Endpoint para cerrar sesión"""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': 'Sesión cerrada exitosamente'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al cerrar sesión: {str(e)}'
        }), 500

@usuario_bp.route('/api/user/current', methods=['GET'])
def get_current_user():
    """Obtener información del usuario actual"""
    try:
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'message': 'No hay sesión activa'
            }), 401
        
        user_id = session.get('user_id')
        result = usuario_service.get_user_by_id(user_id)
        
        return jsonify(result), 200 if result['success'] else 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener usuario: {str(e)}'
        }), 500

@usuario_bp.route('/api/register', methods=['POST'])
def register():
    """Endpoint para registrar nuevos usuarios"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos'
            }), 400
        
        nombre_usuario = data.get('nombre_usuario')
        correo_electronico = data.get('correo_electronico')
        contrasena = data.get('contrasena')
        rol_id = data.get('rol_id', 2)  # Por defecto rol de usuario
        
        if not all([nombre_usuario, correo_electronico, contrasena]):
            return jsonify({
                'success': False,
                'message': 'Todos los campos son requeridos'
            }), 400
        
        # Crear usuario
        result = usuario_service.create_user(nombre_usuario, correo_electronico, contrasena, rol_id)
        
        return jsonify(result), 201 if result['success'] else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error interno del servidor: {str(e)}'
        }), 500

@usuario_bp.route('/api/check-session', methods=['GET'])
def check_session():
    """Verificar si hay una sesión activa"""
    try:
        if session.get('logged_in'):
            return jsonify({
                'success': True,
                'logged_in': True,
                'user': {
                    'id': session.get('user_id'),
                    'username': session.get('username'),
                    'rol_id': session.get('rol_id')
                }
            }), 200
        else:
            return jsonify({
                'success': True,
                'logged_in': False
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al verificar sesión: {str(e)}'
        }), 500
        
@usuario_bp.route('/api/users', methods=['GET'])
def get_users():
    """Obtener lista de usuarios con filtros opcionales
    
    Query params:
    - search: término de búsqueda (nombre o email)
    - rol_id: filtrar por rol
    - activo: filtrar por estado (true/false)
    """
    try:
        # Verificar si hay sesión activa
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'message': 'Acceso denegado'
            }), 401
        
        # Obtener parámetros de búsqueda
        search_term = request.args.get('search')
        rol_id = request.args.get('rol_id', type=int)
        activo_param = request.args.get('activo')
        
        # Convertir activo a booleano si se proporciona
        activo = None
        if activo_param is not None:
            activo = activo_param.lower() in ['true', '1', 'yes']
        
        # Si hay filtros, usar búsqueda; si no, obtener todos
        if search_term or rol_id or activo is not None:
            result = usuario_service.search_users(search_term, rol_id, activo)
        else:
            result = usuario_service.get_all_users()
            
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener usuarios: {str(e)}'
        }), 500

@usuario_bp.route('/api/users/search', methods=['GET'])
def search_users():
    """Endpoint específico para búsqueda de usuarios
    
    Query params:
    - q o query: término de búsqueda
    - rol_id: filtrar por rol
    - activo: filtrar por estado
    """
    try:
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'message': 'Acceso denegado'
            }), 401
        
        search_term = request.args.get('q') or request.args.get('query')
        rol_id = request.args.get('rol_id', type=int)
        activo_param = request.args.get('activo')
        
        activo = None
        if activo_param is not None:
            activo = activo_param.lower() in ['true', '1', 'yes']
        
        result = usuario_service.search_users(search_term, rol_id, activo)
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error en la búsqueda: {str(e)}'
        }), 500
        # http://127.0.0.1:5000/api/users/5
@usuario_bp.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Obtener un usuario específico por ID"""
    try:
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'message': 'Acceso denegado'
            }), 401
        
        result = usuario_service.get_user_by_id(user_id)
        return jsonify(result), 200 if result['success'] else 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener usuario: {str(e)}'
        }), 500
        
@usuario_bp.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Actualizar datos de usuario"""
    try:
        # Verificar sesión
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'message': 'Acceso denegado'
            }), 401
            
        # Obtener datos del body
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos'
            }), 400
            
        result = usuario_service.update_user(user_id, data)
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al actualizar usuario: {str(e)}'
        }), 500
        
@usuario_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Eliminar usuario"""
    try:
        # Verificar sesión
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'message': 'Acceso denegado'
            }), 401
        
        # Prevenir que un usuario se elimine a sí mismo
        if session.get('user_id') == user_id:
            return jsonify({
                'success': False,
                'message': 'No puedes eliminar tu propia cuenta'
            }), 400
            
        result = usuario_service.delete_user(user_id)
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al eliminar usuario: {str(e)}'
        }), 500

@usuario_bp.route('/api/users/<int:user_id>/toggle-active', methods=['PATCH'])
def toggle_user_active(user_id):
    """Activar o desactivar un usuario"""
    try:
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'message': 'Acceso denegado'
            }), 401
        
        # Prevenir que un usuario se desactive a sí mismo
        if session.get('user_id') == user_id:
            return jsonify({
                'success': False,
                'message': 'No puedes desactivar tu propia cuenta'
            }), 400
        
        result = usuario_service.toggle_user_status(user_id)
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al cambiar estado: {str(e)}'
        }), 500

@usuario_bp.route('/api/users/<int:user_id>/unlock', methods=['PATCH'])
def unlock_user(user_id):
    """Desbloquear un usuario manualmente"""
    try:
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'message': 'Acceso denegado'
            }), 401
        
        # Solo administradores pueden desbloquear
        if session.get('rol_id') != 1:
            return jsonify({
                'success': False,
                'message': 'Solo administradores pueden desbloquear usuarios'
            }), 403
        
        result = usuario_service.unlock_user(user_id)
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al desbloquear usuario: {str(e)}'
        }), 500