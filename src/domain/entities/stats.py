from pydantic import BaseModel
from typing import Dict, Any

class SummaryStats(BaseModel):
    total_escolas: int
    total_municipios: int
    indicadores_infra: Dict[str, float]
    por_dependencia: Dict[str, int]
    por_zona: Dict[str, int]

    @classmethod
    def from_dict(cls, data: Any):
        if isinstance(data, cls):
            return data
        data = data or {}
        return cls(
            total_escolas=data.get("total_escolas", 0),
            total_municipios=data.get("total_municipios", 0),
            indicadores_infra=data.get("indicadores_infra", {}),
            por_dependencia=data.get("por_dependencia", {}),
            por_zona=data.get("por_zona", {})
        )