
class SchoolValidator:
    def __init__(self, municipio_id_ibge: str, escola_id_inep: int,
                 escola_nome: str, score_risco: float):
        self._municipio_id_ibge = municipio_id_ibge
        self._escola_id_inep = escola_id_inep
        self._escola_nome = escola_nome
        self._score_risco = score_risco
        self._validate()   

    def _validate(self):
        if not self._municipio_id_ibge or len(self._municipio_id_ibge) != 7:
            raise ValueError("municipio_id_ibge deve ter 7 dígitos")
        
        if self._escola_id_inep <= 0:
            raise ValueError("escola_id_inep deve ser positivo")
        
        if not self._escola_nome or len(self._escola_nome.strip()) == 0:
            raise ValueError("escola_nome é obrigatório")
        
        if not 0 <= self._score_risco <= 100:
            raise ValueError("score_risco deve estar entre 0 e 100")