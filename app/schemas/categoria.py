from pydantic import BaseModel, ConfigDict, Field


class CategoriaCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=50, examples=["Comida"])


class CategoriaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
