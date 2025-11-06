# models/usuario.py
import hashlib
import uuid as _uuid
from datetime import datetime
import bcrypt


class Usuario:
    """Modelo de usuario que mapea la tabla `users`.

    Columnas esperadas: id, uuid, nombre, email, password_hash, rol_id, activo,
    ultimo_acceso, intentos_fallidos, bloqueado_hasta, created_at, updated_at
    """

    def __init__(self, id=None, uuid=None, nombre=None, email=None, password_hash=None,
                 rol_id=None, activo=1, ultimo_acceso=None, intentos_fallidos=0,
                 bloqueado_hasta=None, created_at=None, updated_at=None):
        self.id = id
        self.uuid = uuid
        self.nombre = nombre
        self.email = email
        self.password_hash = password_hash
        self.rol_id = rol_id
        self.activo = activo
        self.ultimo_acceso = ultimo_acceso
        self.intentos_fallidos = intentos_fallidos
        self.bloqueado_hasta = bloqueado_hasta
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def hash_password(password: str) -> str:
        """Genera un hash de contraseña usando bcrypt."""
        if password is None:
            return None
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hashed.decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """Verifica la contraseña contra el hash almacenado.

        Soporta hashes bcrypt (prefijo $2b$/$2a$/$2y$) y legacy SHA-256.
        """
        if self.password_hash is None:
            return False

        ph = str(self.password_hash)
        # bcrypt hashes start with $2b$ or $2a$ or $2y$
        if ph.startswith('$2a$') or ph.startswith('$2b$') or ph.startswith('$2y$'):
            try:
                return bcrypt.checkpw(password.encode('utf-8'), ph.encode('utf-8'))
            except Exception:
                return False

        # Fallback: legacy SHA-256 comparison
        return ph == hashlib.sha256(password.encode('utf-8')).hexdigest()

    @staticmethod
    def from_dict(d: dict):
        if not d:
            return None
        # soportar claves con mayúsculas/minúsculas y alias
        return Usuario(
            id=d.get('id') or d.get('Id'),
            uuid=d.get('uuid') or d.get('UUID'),
            nombre=d.get('nombre') or d.get('nombre_usuario') or d.get('username'),
            email=d.get('email') or d.get('correo_electronico'),
            password_hash=d.get('password_hash') or d.get('contrasena') or d.get('password'),
            rol_id=d.get('rol_id'),
            activo=d.get('activo'),
            ultimo_acceso=d.get('ultimo_acceso'),
            intentos_fallidos=d.get('intentos_fallidos'),
            bloqueado_hasta=d.get('bloqueado_hasta'),
            created_at=d.get('created_at'),
            updated_at=d.get('updated_at')
        )

    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'nombre': self.nombre,
            'username': self.nombre,  # alias útil para el frontend
            'email': self.email,
            'rol_id': self.rol_id,
            'activo': self.activo,
            'ultimo_acceso': self.ultimo_acceso,
            'intentos_fallidos': self.intentos_fallidos,
            'bloqueado_hasta': self.bloqueado_hasta,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @staticmethod
    def new_from_plain_password(nombre: str, email: str, plain_password: str, rol_id: int = None):
        """Crear instancia lista para insertar: genera uuid, hashea contraseña y timestamps."""
        now = datetime.utcnow()
        return Usuario(
            uuid=str(_uuid.uuid4()),
            nombre=nombre,
            email=email,
            password_hash=Usuario.hash_password(plain_password),
            rol_id=rol_id,
            activo=1,
            created_at=now,
            updated_at=now
        )

