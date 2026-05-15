from typing import List
from src.domain.entities.state_summary import StateSummary, EducacaoStateStats, SocioeconomicoStateStats
from src.domain.entities.city_aggregation import CityAggregation

class StateSummaryFactory:
    """
    Factory responsável por encapsular as regras de negócio e matemática 
    para agregar os dados de vários municípios em um resumo estadual.
    """

    @staticmethod
    def _safe_div(num: float, den: float) -> float | None:
        """Helper para evitar divisão por zero e aplicar arredondamento padrão."""
        return round(num / den, 2) if den > 0 else None

    @classmethod
    def _calc_educacao(cls, cities: List[CityAggregation]) -> EducacaoStateStats:
        total_escolas = sum(c.educacao.total_escolas for c in cities)
        total_alunos = sum(c.educacao.total_alunos for c in cities)

        escolas_biblioteca = sum(c.educacao.total_escolas * c.educacao.pct_com_biblioteca for c in cities)
        escolas_internet = sum(c.educacao.total_escolas * c.educacao.pct_com_internet for c in cities)
        escolas_lab = sum(c.educacao.total_escolas * c.educacao.pct_com_lab_informatica for c in cities)
        escolas_sem_acess = sum(c.educacao.total_escolas * c.educacao.pct_sem_acessibilidade for c in cities)

        soma_ideb_inic = sum(c.educacao.ideb_iniciais * c.educacao.total_alunos for c in cities if c.educacao.ideb_iniciais > 0)
        alunos_ideb_inic = sum(c.educacao.total_alunos for c in cities if c.educacao.ideb_iniciais > 0)

        soma_ideb_fin = sum(c.educacao.ideb_finais * c.educacao.total_alunos for c in cities if c.educacao.ideb_finais > 0)
        alunos_ideb_fin = sum(c.educacao.total_alunos for c in cities if c.educacao.ideb_finais > 0)

        return EducacaoStateStats(
            total_escolas=total_escolas,
            total_alunos=total_alunos,
            pct_com_biblioteca=cls._safe_div(escolas_biblioteca, total_escolas),
            pct_com_internet=cls._safe_div(escolas_internet, total_escolas),
            pct_com_lab_informatica=cls._safe_div(escolas_lab, total_escolas),
            pct_sem_acessibilidade=cls._safe_div(escolas_sem_acess, total_escolas),
            avg_ideb_iniciais=cls._safe_div(soma_ideb_inic, alunos_ideb_inic),
            avg_ideb_finais=cls._safe_div(soma_ideb_fin, alunos_ideb_fin)
        )

    @classmethod
    def _calc_socioeconomico(cls, cities: List[CityAggregation]) -> SocioeconomicoStateStats:
        pop_total = sum(c.socioeconomico.populacao for c in cities)
        
        soma_desemprego = sum(
            c.socioeconomico.taxa_desemprego * c.socioeconomico.populacao 
            for c in cities if c.socioeconomico.populacao > 0
        )

        return SocioeconomicoStateStats(
            populacao_total=pop_total,
            indicadores={"taxa_desemprego_media": cls._safe_div(soma_desemprego, pop_total)}
        )

    @classmethod
    def create_from_cities(cls, sg_uf: str, cities: List[CityAggregation]) -> StateSummary:
        """Método público que constrói o objeto final."""
        return StateSummary(
            sg_uf=sg_uf.upper(),
            educacao=cls._calc_educacao(cities),
            socioeconomico=cls._calc_socioeconomico(cities)
        )