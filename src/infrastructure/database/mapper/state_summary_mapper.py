from src.domain.entities.city_aggregation import CityAggregation, CityEducacao, CitySocioeconomico
from typing import Any

class StateSummaryMapper:
    @staticmethod
    def _extract_number(val: Any) -> float:
        """Centraliza a lógica de extrair números de dicionários do MongoDB."""
        if isinstance(val, dict):
            return float(val.get("total", val.get("valor", 0)))
        return float(val) if val is not None else 0.0

    @classmethod
    def to_entity(cls, data: dict) -> CityAggregation:
        educacao = data.get("educacao") or {}
        socio = data.get("socioeconomico") or {}
        
        return CityAggregation(
            educacao=CityEducacao(
                total_escolas=int(cls._extract_number(educacao.get("totalEscolas"))),
                total_alunos=int(cls._extract_number(educacao.get("totalMatriculas"))),
                pct_com_biblioteca=cls._extract_number(educacao.get("pctComBiblioteca")),
                pct_com_internet=cls._extract_number(educacao.get("pctComInternet")),
                pct_com_lab_informatica=cls._extract_number(educacao.get("pctComLabInformatica")),
                pct_sem_acessibilidade=cls._extract_number(educacao.get("pctSemAcessibilidade")),
                ideb_iniciais=cls._extract_number(educacao.get("mediaIdebAnosIniciais")),
                ideb_finais=cls._extract_number(educacao.get("mediaIdebAnosFinals")),
            ),
            socioeconomico=CitySocioeconomico(
                populacao=int(cls._extract_number(socio.get("populacao"))),
                taxa_desemprego=cls._extract_number(socio.get("taxaDesemprego"))
            )
        )