
from pydantic import BaseModel, PositiveInt
import json

class SingleValue(BaseModel):
    name: str
    description: str
    value: float

class EnumValue(BaseModel):
    name: str
    values: list[str]
    type: str

class Ifc2Uni(BaseModel):
    id: int  
    name: SingleValue 
    functional_properties: dict[SingleValue]  
    color: SingleValue
    loudness: SingleValue
    conform: SingleValue
    description: SingleValue
    meaning: SingleValue
    name: SingleValue
    weight: SingleValue
    density: SingleValue
    surface_structure: SingleValue
    classification: SingleValue
    price: float
    metadata: str


    