from pydantic import BaseModel


class Endereco(BaseModel):
    bairro: str = ""
    cep: str = ""
    logradouro: str = ""
    municipio: str = ""
    numero: str = ""
    uf: str = ""
