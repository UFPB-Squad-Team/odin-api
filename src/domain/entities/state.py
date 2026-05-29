from pydantic import BaseModel

class State(BaseModel):
    id: str
    nome: str
    sigla: str