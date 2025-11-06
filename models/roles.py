from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Role:
    """Modelo de datos para la tabla 'roles'."""
    id: Optional[int] = field(default=None)
    nombre: str
    descripcion: Optional[str] = field(default=None)
    created_at: Optional[datetime] = field(default=None)
    
    @staticmethod
    def from_dict(data: dict):
        """Crea una instancia de Role a partir del diccionario de la BD."""
        return Role(
            id=data.get('id'),
            nombre=data.get('nombre'),
            descripcion=data.get('descripcion'),
            created_at=data.get('created_at') 
        )