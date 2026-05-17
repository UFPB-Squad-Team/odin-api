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

        # Weighted averages by number of schools (infrastructure percentages)
        def _pct_weighted_by_schools(field: str) -> float | None:
            numerator = sum(
                c.educacao.total_escolas * getattr(c.educacao, field)
                for c in cities if c.educacao.total_escolas > 0
            )
            return cls._safe_div(numerator, total_escolas)

        # Weighted averages by number of students (academic indicators)
        def _avg_weighted_by_alunos(field: str) -> float | None:
            numerator = sum(
                getattr(c.educacao, field) * c.educacao.total_alunos
                for c in cities if getattr(c.educacao, field) > 0
            )
            denominator = sum(
                c.educacao.total_alunos
                for c in cities if getattr(c.educacao, field) > 0
            )
            return cls._safe_div(numerator, denominator)

        return EducacaoStateStats(
            total_escolas=total_escolas,
            total_alunos=total_alunos,
            # Infrastructure (weighted by schools)
            pct_com_biblioteca=_pct_weighted_by_schools("pct_com_biblioteca"),
            pct_com_internet=_pct_weighted_by_schools("pct_com_internet"),
            pct_com_internet_alunos=_pct_weighted_by_schools("pct_com_internet_alunos"),
            pct_com_lab_informatica=_pct_weighted_by_schools("pct_com_lab_informatica"),
            pct_com_lab_ciencias=_pct_weighted_by_schools("pct_com_lab_ciencias"),
            pct_sem_acessibilidade=_pct_weighted_by_schools("pct_sem_acessibilidade"),
            pct_com_agua_potavel=_pct_weighted_by_schools("pct_com_agua_potavel"),
            pct_com_energia_publica=_pct_weighted_by_schools("pct_com_energia_publica"),
            pct_com_esgoto_rede_publica=_pct_weighted_by_schools("pct_com_esgoto_rede_publica"),
            pct_com_coleta_lixo=_pct_weighted_by_schools("pct_com_coleta_lixo"),
            pct_com_quadra_esportes=_pct_weighted_by_schools("pct_com_quadra_esportes"),
            pct_com_cozinha=_pct_weighted_by_schools("pct_com_cozinha"),
            pct_com_refeitorio=_pct_weighted_by_schools("pct_com_refeitorio"),
            # IDEB (weighted by students)
            avg_ideb_iniciais=_avg_weighted_by_alunos("ideb_iniciais"),
            avg_ideb_finais=_avg_weighted_by_alunos("ideb_finais"),
            avg_ideb_ensino_medio=_avg_weighted_by_alunos("ideb_ensino_medio"),
            # AFD (weighted by students)
            avg_afd_anos_iniciais=_avg_weighted_by_alunos("media_afd_anos_iniciais"),
            avg_afd_anos_finais=_avg_weighted_by_alunos("media_afd_anos_finais"),
            avg_afd_ensino_medio=_avg_weighted_by_alunos("media_afd_ensino_medio"),
            # TDI (weighted by students)
            avg_tdi_anos_iniciais=_avg_weighted_by_alunos("media_tdi_anos_iniciais"),
            avg_tdi_anos_finais=_avg_weighted_by_alunos("media_tdi_anos_finais"),
            avg_tdi_ensino_medio=_avg_weighted_by_alunos("media_tdi_ensino_medio"),
            # Approval rates (weighted by students)
            avg_taxa_aprovacao_ai=_avg_weighted_by_alunos("media_taxa_aprovacao_ai"),
            avg_taxa_aprovacao_af=_avg_weighted_by_alunos("media_taxa_aprovacao_af"),
            avg_taxa_aprovacao_em=_avg_weighted_by_alunos("media_taxa_aprovacao_em"),
            # Dropout rates (weighted by students)
            avg_taxa_abandono_ai=_avg_weighted_by_alunos("media_taxa_abandono_ai"),
            avg_taxa_abandono_af=_avg_weighted_by_alunos("media_taxa_abandono_af"),
            avg_taxa_abandono_em=_avg_weighted_by_alunos("media_taxa_abandono_em"),
            # Teachers with higher education (weighted by students)
            avg_docentes_superior_ai=_avg_weighted_by_alunos("media_docentes_superior_ai"),
            avg_docentes_superior_af=_avg_weighted_by_alunos("media_docentes_superior_af"),
            avg_docentes_superior_em=_avg_weighted_by_alunos("media_docentes_superior_em"),
            # Hours per day (weighted by students)
            avg_horas_aula_ai=_avg_weighted_by_alunos("media_horas_aula_ai"),
            avg_horas_aula_af=_avg_weighted_by_alunos("media_horas_aula_af"),
            avg_horas_aula_em=_avg_weighted_by_alunos("media_horas_aula_em"),
            # Students per class (weighted by students)
            avg_alunos_turma_ai=_avg_weighted_by_alunos("media_alunos_turma_ai"),
            avg_alunos_turma_af=_avg_weighted_by_alunos("media_alunos_turma_af"),
            avg_alunos_turma_em=_avg_weighted_by_alunos("media_alunos_turma_em"),
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