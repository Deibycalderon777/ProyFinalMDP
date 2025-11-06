from flask import Blueprint, jsonify, request
from services.roles_service import RolesService # Importamos la clase de servicio

# Inicializar Blueprint con prefijo /api/roles
role_bp = Blueprint('role_bp', __name__, url_prefix='/api/roles')

# Inicializamos el servicio (contiene la simulación de la BD).
roles_service = RolesService()

@role_bp.route('/', methods=['GET'])
def get_roles():
    """Endpoint GET /api/roles - Obtener todos los roles."""
    response = roles_service.obtener_todos()
    # Determina el código de estado: 200 si es exitoso, o usa 'status' del servicio si falla
    status_code = response.get('status', 200 if response['success'] else 500)
    return jsonify(response), status_code

@role_bp.route('/<int:role_id>', methods=['GET'])
def get_role_by_id(role_id):
    """Endpoint GET /api/roles/<int:role_id> - Obtener rol por ID."""
    response = roles_service.obtener_por_id(role_id)
    # Determina el código de estado: 200 si es exitoso, o usa 'status' (ej. 404)
    status_code = response.get('status', 200 if response['success'] else 500)
    return jsonify(response), status_code

@role_bp.route('/', methods=['POST'])
def create_role():
    """Endpoint POST /api/roles - Crear un nuevo rol."""
    data = request.get_json()
    nombre = data.get('nombre', '')
    descripcion = data.get('descripcion', '')
    
    response = roles_service.crear_rol(nombre, descripcion)
    # Determina el código de estado: 201 (Created) si es exitoso, o usa 'status' si falla
    status_code = response.get('status', 201 if response['success'] else 500)
    return jsonify(response), status_code

# ==========================================================
# NUEVA FUNCIÓN: EDITAR ROL (PUT)
# ==========================================================
@role_bp.route('/<int:role_id>', methods=['PUT'])
def update_role(role_id):
    """Endpoint PUT /api/roles/<int:role_id> - Actualizar un rol existente."""
    data = request.get_json()
    nombre = data.get('nombre', None)
    descripcion = data.get('descripcion', None)
    
    # Se pasa 'None' si no están en el cuerpo, el servicio debe manejar esto
    response = roles_service.actualizar_rol(role_id, nombre, descripcion)
    
    # Determina el código de estado: 200 si es exitoso, o usa 'status' si falla (ej. 404, 400)
    status_code = response.get('status', 200 if response['success'] else 500)
    return jsonify(response), status_code

# ==========================================================
# NUEVA FUNCIÓN: ELIMINAR ROL (DELETE)
# ==========================================================
@role_bp.route('/<int:role_id>', methods=['DELETE'])
def delete_role(role_id):
    """Endpoint DELETE /api/roles/<int:role_id> - Eliminar un rol."""
    response = roles_service.eliminar_rol(role_id)
    
    # Determina el código de estado: 200 si es exitoso, o usa 'status' si falla (ej. 404, 400)
    status_code = response.get('status', 200 if response['success'] else 500)
    return jsonify(response), status_code