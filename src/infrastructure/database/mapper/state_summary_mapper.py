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
                pct_com_internet_alunos=cls._extract_number(educacao.get("pctComInternetAlunos")),
                pct_com_lab_informatica=cls._extract_number(educacao.get("pctComLaboratorioInformatica") or educacao.get("pctComLabInformatica")),
                pct_com_lab_ciencias=cls._extract_number(educacao.get("pctComLaboratorioCiencias")),
                pct_sem_acessibilidade=cls._extract_number(educacao.get("pctSemAcessibilidade")),
                pct_com_agua_potavel=cls._extract_number(educacao.get("pctComAguaPotavel")),
                pct_com_energia_publica=cls._extract_number(educacao.get("pctComEnergiaPublica")),
                pct_com_esgoto_rede_publica=cls._extract_number(educacao.get("pctComEsgotoRedePublica")),
                pct_com_coleta_lixo=cls._extract_number(educacao.get("pctComColetaLixo")),
                pct_com_quadra_esportes=cls._extract_number(educacao.get("pctComQuadraEsportes")),
                pct_com_cozinha=cls._extract_number(educacao.get("pctComCozinha")),
                pct_com_refeitorio=cls._extract_number(educacao.get("pctComRefeitorio")),
                ideb_iniciais=cls._extract_number(educacao.get("mediaIdebAnosIniciais")),
                ideb_finais=cls._extract_number(educacao.get("mediaIdebAnosFinals")),
                ideb_ensino_medio=cls._extract_number(educacao.get("mediaIdebEnsinoMedio")),
                media_afd_anos_iniciais=cls._extract_number(educacao.get("mediaAfdAnosIniciais")),
                media_afd_anos_finais=cls._extract_number(educacao.get("mediaAfdAnosFinais")),
                media_afd_ensino_medio=cls._extract_number(educacao.get("mediaAfdEnsinoMedio")),
                media_tdi_anos_iniciais=cls._extract_number(educacao.get("mediaTdiAnosIniciais")),
                media_tdi_anos_finais=cls._extract_number(educacao.get("mediaTdiAnosFinais")),
                media_tdi_ensino_medio=cls._extract_number(educacao.get("mediaTdiEnsinoMedio")),
                media_taxa_aprovacao_ai=cls._extract_number(educacao.get("mediaTaxaAprovacaoAi")),
                media_taxa_aprovacao_af=cls._extract_number(educacao.get("mediaTaxaAprovacaoAf")),
                media_taxa_aprovacao_em=cls._extract_number(educacao.get("mediaTaxaAprovacaoEm")),
                media_taxa_abandono_ai=cls._extract_number(educacao.get("mediaTaxaAbandonoAi")),
                media_taxa_abandono_af=cls._extract_number(educacao.get("mediaTaxaAbandonoAf")),
                media_taxa_abandono_em=cls._extract_number(educacao.get("mediaTaxaAbandonoEm")),
                media_docentes_superior_ai=cls._extract_number(educacao.get("mediaDocentesSuperiorAi")),
                media_docentes_superior_af=cls._extract_number(educacao.get("mediaDocentesSuperiorAf")),
                media_docentes_superior_em=cls._extract_number(educacao.get("mediaDocentesSuperiorEm")),
                media_horas_aula_ai=cls._extract_number(educacao.get("mediaHorasAulaAi")),
                media_horas_aula_af=cls._extract_number(educacao.get("mediaHorasAulaAf")),
                media_horas_aula_em=cls._extract_number(educacao.get("mediaHorasAulaEm")),
                media_alunos_turma_ai=cls._extract_number(educacao.get("mediaAlunosTurmaAi")),
                media_alunos_turma_af=cls._extract_number(educacao.get("mediaAlunosTurmaAf")),
                media_alunos_turma_em=cls._extract_number(educacao.get("mediaAlunosTurmaEm")),
            ),
            socioeconomico=CitySocioeconomico(
                populacao=int(cls._extract_number(socio.get("populacao"))),
                taxa_desemprego=cls._extract_number(socio.get("taxaDesemprego"))
            )
        )