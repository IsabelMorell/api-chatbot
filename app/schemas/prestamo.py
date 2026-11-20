from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# clase PrestamoEntrada (BaseModel) con las 6 variables del modelo, con sus rangos (ver enunciado).
#       Debe rechazar campos que no existan.
# field_validator (con classmethod) para antiguedad_laboral_anios: no puede ser incoherente con la edad.
# clase PrediccionSalida con probabilidad_impago (entre 0 y 1) y decision (aprobar, revisar o rechazar).

class PrestamoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edad: int = Field(ge=18, le=75)
    ingresos_mensuales: float = Field(gt=0)
    importe_prestamo: float = Field(gt=0)
    plazo_meses: int = Field(ge=6, le=84) 
    antiguedad_laboral_anios: int = Field(ge=0, le=50)
    impagos_previos: int = Field(ge=0, le=20)
    
    @field_validator("antiguedad_laboral_anios")
    @classmethod
    def validar_antiguedad(cls, valor, info):
        edad = info.data.get("edad")

        if edad is not None and valor > edad - 16:
            raise ValueError(
                "La antigüedad laboral no puede ser superior "
                "a los años transcurridos desde los 16 años."
            )

        return valor

class PrediccionSalida(BaseModel):
    probabilidad_impago: float = Field(ge=0, le=1)
    decision: Literal["aprobar", "revisar", "rechazar"]
