from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


# --- ENUMS ---
class Genero(str, Enum):
    M = "M"
    F = "F"
    OTRO = "Otro"
    MASCULINO = "Masculino"
    FEMENINO = "Femenino"

class Moneda(str, Enum):
    CRC = "CRC"
    USD = "USD"

class canal(str, Enum):
    WEB = "WEB"
    TIENDA = "TIENDA"
    PARTNER = "PARTNER"
     
# --- MODELOS BASE ---
class Cliente(BaseModel):
    id: str
    nombre: str
    genero: Genero
    pais: str

class Categoria(BaseModel):
    id: str
    nombre: str

class Producto(BaseModel):
    id: str
    nombre: str
    categoria: Optional[str] = None
    sku: Optional[str] = None
    codigo_alt: Optional[str] = None
    codigo_mongo: Optional[str] = None

# --- RELACIONES / SUBESQUEMAS ---
class Item(BaseModel):
    producto_id: str
    cantidad: int = Field(..., ge=1)
    precio_unit: float = Field(..., ge=0)



# --- ORDER  ---
class Order(BaseModel):
    id: Optional[str] = None
    cliente_id: str
    fecha: datetime
    canal: canal
    moneda: Moneda
    total: float = Field(..., ge=0)
    items: List[Item] = Field(..., min_items=1)
