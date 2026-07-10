from __future__ import annotations

import logging
from typing import Any

from src.domain.entities.report import MunicipioDossierData, StateDossierData

logger = logging.getLogger(__name__)


class ReportDataService:
    def __init__(
        self,
        escolas_collection: Any,
        municipio_collection: Any,
        bairro_collection: Any,
    ) -> None:
        self._escolas = escolas_collection
        self._municipios = municipio_collection
        self._bairros = bairro_collection

    async def get_municipio_dossier_data(
        self,
        municipio_id_ibge: str,
    ) -> MunicipioDossierData | None:
        municipio = await self._get_municipio_info(municipio_id_ibge)
        if not municipio:
            logger.warning("Municipio %s not found", municipio_id_ibge)
            return None

        municipio_nome = (
            municipio.get("municipio") or municipio.get("nm_municipio") or ""
        )
        uf = municipio.get("sg_uf") or municipio.get("uf") or ""
        educacao = municipio.get("educacao") or {}
        socioeconomico = municipio.get("socioeconomico") or {}

        top_escolas = await self._get_top_escolas(
            municipio_id_ibge, municipio_nome, limit=5
        )
        top_escolas_named = []
        for school in top_escolas:
            top_escolas_named.append(
                {
                    "nome": school.get("escolaNome") or school.get("escola_nome") or "",
                    "ideb": school.get("ideb") or school.get("ideb_media") or 0,
                    "dependencia": school.get("dependenciaAdm")
                    or school.get("dependencia_adm")
                    or "",
                    "localizacao": school.get("tipoLocalizacao")
                    or school.get("tipo_localizacao")
                    or "",
                }
            )

        escolas_data = await self._aggregate_escolas_por_municipio(
            municipio_id_ibge, municipio_nome
        )

        infraestrutura = {}
        for key, db_key in [
            ("Internet", "pctComInternet"),
            ("Biblioteca", "pctComBiblioteca"),
            ("Lab. Informática", "pctComLaboratorioInformatica"),
            ("Lab. Ciências", "pctComLaboratorioCiencias"),
            ("Quadra Esportiva", "pctComQuadraEsportes"),
            ("Acessibilidade PcD", "pctComAcessibilidade"),
            ("Água Potável", "pctComAguaPotavel"),
            ("Energia Elétrica", "pctComEnergiaPublica"),
            ("Coleta de Lixo", "pctComColetaLixo"),
            ("Esgoto Rede Pública", "pctComEsgotoRedePublica"),
            ("Cozinha", "pctComCozinha"),
            ("Refeitório", "pctComRefeitorio"),
            ("Internet p/ Alunos", "pctComInternetAlunos"),
        ]:
            val = educacao.get(db_key)
            if val is not None:
                infraestrutura[key] = float(val)

        for key, aggr_key in [
            ("Internet", "pct_internet"),
            ("Biblioteca", "pct_biblioteca"),
            ("Lab. Informática", "pct_lab_informatica"),
            ("Lab. Ciências", "pct_lab_ciencias"),
            ("Quadra Esportiva", "pct_quadra"),
            ("Acessibilidade PcD", "pct_acessibilidade"),
            ("Água Potável", "pct_agua_potavel"),
        ]:
            if key not in infraestrutura:
                val = escolas_data.get(aggr_key)
                if val is not None:
                    infraestrutura[key] = float(val)

        ideb_por_etapa = {}
        aprovacao_por_etapa = {}
        abandono_por_etapa = {}
        distorcao_idade_serie_por_etapa = {}
        adequacao_docente_por_etapa = {}
        docentes_superior_por_etapa = {}
        horas_aula_por_etapa = {}
        alunos_por_turma_etapa = {}

        for stage in ["Anos Iniciais", "Anos Finais", "Ensino Médio"]:
            stage_key = stage.replace(" ", "")
            val = educacao.get(f"mediaIdeb{stage_key}")
            if val is not None:
                ideb_por_etapa[stage] = float(val)

            suffix_map = {
                "Anos Iniciais": "Ai",
                "Anos Finais": "Af",
                "Ensino Médio": "Em",
            }
            suffix = suffix_map[stage]

            val = educacao.get(f"mediaTaxaAprovacao{suffix}")
            if val is not None:
                aprovacao_por_etapa[stage] = float(val)

            val = educacao.get(f"mediaTaxaAbandono{suffix}")
            if val is not None:
                abandono_por_etapa[stage] = float(val)

            val = educacao.get(f"mediaTdi{suffix}")
            if val is not None:
                distorcao_idade_serie_por_etapa[stage] = float(val)

            val = educacao.get(f"mediaAfd{suffix}")
            if val is not None:
                adequacao_docente_por_etapa[stage] = float(val)

            val = educacao.get(f"mediaDocentesSuperior{suffix}")
            if val is not None:
                docentes_superior_por_etapa[stage] = float(val)

            val = educacao.get(f"mediaHorasAula{suffix}")
            if val is not None:
                horas_aula_por_etapa[stage] = float(val)

            val = educacao.get(f"mediaAlunosTurma{suffix}")
            if val is not None:
                alunos_por_turma_etapa[stage] = float(val)

        if not ideb_por_etapa:
            ideb_iniciais = escolas_data.get("avg_ideb_iniciais")
            ideb_finais = escolas_data.get("avg_ideb_finais")
            if ideb_iniciais is not None:
                ideb_por_etapa["Anos Iniciais"] = float(ideb_iniciais)
            if ideb_finais is not None:
                ideb_por_etapa["Anos Finais"] = float(ideb_finais)

        if not aprovacao_por_etapa:
            aprov_media = escolas_data.get("taxa_aprovacao_media")
            if aprov_media is not None:
                aprovacao_por_etapa["Anos Iniciais"] = float(aprov_media)
                aprovacao_por_etapa["Anos Finais"] = float(aprov_media)

        populacao = socioeconomico.get("populacao") or {}
        estrutura_etaria = {}
        if "faixaEtaria" in populacao:
            for faixa, val in populacao["faixaEtaria"].items():
                if val is not None:
                    estrutura_etaria[faixa] = float(val)
        else:
            for key in [
                "pctCriancas0a9",
                "pctIdosos60Mais",
                "pctJovens15a29",
                "pctAdultos30a59",
            ]:
                if key in socioeconomico.get("estruturaEtaria", {}):
                    estrutura_etaria[
                        key.replace("pct", "")
                        .replace("0a9", "0-9")
                        .replace("60Mais", "60+")
                    ] = float(socioeconomico["estruturaEtaria"][key])

        raca = {}
        if "raca" in socioeconomico:
            for chave, val in socioeconomico["raca"].items():
                if val is not None:
                    raca[chave] = float(val)

        genero = {}
        if "genero" in socioeconomico:
            for chave, val in socioeconomico["genero"].items():
                if val is not None:
                    genero[chave] = float(val)

        razao_dependencia = None
        if "razaoDependencia" in socioeconomico.get("estruturaEtaria", {}):
            razao_dependencia = self._safe_float(
                socioeconomico["estruturaEtaria"]["razaoDependencia"]
            )

        saneamento = {}
        if "saneamento" in socioeconomico:
            for chave, val in socioeconomico["saneamento"].items():
                if val is not None:
                    saneamento[chave] = float(val)

        habitacao = {}
        if "habitacao" in socioeconomico:
            for chave, val in socioeconomico["habitacao"].items():
                if val is not None:
                    habitacao[chave] = float(val)

        total_domicilios = None
        media_moradores_domicilio = None
        if "populacao" in socioeconomico:
            total_domicilios = self._safe_int(
                socioeconomico["populacao"].get("totalDomicilios")
            )
            media_moradores_domicilio = self._safe_float(
                socioeconomico["populacao"].get("mediaMoradoresPorDomicilio")
            )

        taxa_analfabetismo = None
        if "educacaoPopulacao" in socioeconomico:
            taxa_analfabetismo = self._safe_float(
                socioeconomico["educacaoPopulacao"].get("taxaAnalfabetismo15Mais")
            )

        pct_responsavel_feminino = None
        if "familia" in socioeconomico:
            pct_responsavel_feminino = self._safe_float(
                socioeconomico["familia"].get("pctResponsavelFeminino")
            )

        obitos_domicilios = None
        obitos_infantis_0a4 = None
        if "mortalidade" in socioeconomico:
            obitos_domicilios = self._safe_int(
                socioeconomico["mortalidade"].get("totalObitosDomicilios")
            )
            obitos_infantis_0a4 = self._safe_int(
                socioeconomico["mortalidade"].get("obitosInfantis0a4")
            )

        ano_referencia_socioeconomico = None
        fonte_socioeconomico = None
        if "anoReferencia" in socioeconomico:
            ano_referencia_socioeconomico = self._safe_int(
                socioeconomico["anoReferencia"]
            )
        if "fonte" in socioeconomico:
            fonte_socioeconomico = socioeconomico["fonte"]

        return MunicipioDossierData(
            municipio_id=municipio_id_ibge,
            municipio_nome=municipio_nome,
            uf=uf,
            total_escolas=educacao.get("totalEscolas", 0),
            total_alunos=educacao.get("totalMatriculas", 0),
            total_bairros=educacao.get("totalBairros", 0),
            ideb_por_etapa=ideb_por_etapa,
            aprovacao_por_etapa=aprovacao_por_etapa,
            abandono_por_etapa=abandono_por_etapa,
            distorcao_idade_serie_por_etapa=distorcao_idade_serie_por_etapa,
            adequacao_docente_por_etapa=adequacao_docente_por_etapa,
            docentes_superior_por_etapa=docentes_superior_por_etapa,
            horas_aula_por_etapa=horas_aula_por_etapa,
            alunos_por_turma_etapa=alunos_por_turma_etapa,
            infraestrutura=infraestrutura,
            escolas_por_dependencia=escolas_data.get("por_dependencia", {}),
            escolas_por_zona=escolas_data.get("por_zona", {}),
            matriculas_por_etapa=escolas_data.get("matriculas_por_etapa", {}),
            top_escolas=top_escolas_named,
            estrutura_etaria=estrutura_etaria,
            raca=raca,
            genero=genero,
            razao_dependencia=razao_dependencia,
            saneamento=saneamento,
            habitacao=habitacao,
            total_domicilios=total_domicilios,
            media_moradores_domicilio=media_moradores_domicilio,
            taxa_analfabetismo=taxa_analfabetismo,
            pct_responsavel_feminino=pct_responsavel_feminino,
            obitos_domicilios=obitos_domicilios,
            obitos_infantis_0a4=obitos_infantis_0a4,
            ano_referencia_socioeconomico=ano_referencia_socioeconomico,
            fonte_socioeconomico=fonte_socioeconomico,
            populacao_total=self._safe_int(populacao.get("total")),
            indicadores_indisponiveis=[],
        )

    async def _get_municipio_info(
        self, municipio_id_ibge: str
    ) -> dict[str, Any] | None:
        for candidate in self._id_candidates(municipio_id_ibge):
            for field in (
                "municipioIdIbge",
                "municipio_id_ibge",
                "co_municipio",
                "idIbge",
            ):
                doc = await self._municipios.find_one(
                    {field: candidate},
                    projection={
                        "municipio": 1,
                        "nm_municipio": 1,
                        "sg_uf": 1,
                        "uf": 1,
                        "socioeconomico": 1,
                        "educacao": 1,
                    },
                )
                if doc:
                    return doc
        return None

    async def _aggregate_escolas_por_municipio(
        self,
        municipio_id_ibge: str,
        municipio_nome: str,
    ) -> dict[str, Any]:
        match_conditions = self._municipio_match(municipio_id_ibge)

        pipeline = [
            {"$match": match_conditions},
            {
                "$group": {
                    "_id": None,
                    "total_escolas": {"$sum": 1},
                    "total_alunos": {
                        "$sum": {"$ifNull": ["$matriculas.totalAlunos", 0]}
                    },
                    "avg_taxa_aprovacao": {
                        "$avg": {
                            "$avg": [
                                {
                                    "$ifNull": [
                                        "$indicadores.fundamentalAnosIniciais.taxaAprovacao",
                                        0,
                                    ]
                                },
                                {
                                    "$ifNull": [
                                        "$indicadores.fundamentalAnosFinais.taxaAprovacao",
                                        0,
                                    ]
                                },
                            ]
                        }
                    },
                    "avg_taxa_reprovacao": {
                        "$avg": {
                            "$avg": [
                                {
                                    "$ifNull": [
                                        "$indicadores.fundamentalAnosIniciais.taxaReprovacao",
                                        0,
                                    ]
                                },
                                {
                                    "$ifNull": [
                                        "$indicadores.fundamentalAnosFinais.taxaReprovacao",
                                        0,
                                    ]
                                },
                            ]
                        }
                    },
                    "avg_ideb_iniciais": {"$avg": "$ideb.anosIniciais"},
                    "avg_ideb_finais": {"$avg": "$ideb.anosFinais"},
                    "pct_internet": {
                        "$avg": {
                            "$cond": [
                                {"$eq": ["$infraestrutura.possuiInternet", True]},
                                100,
                                0,
                            ]
                        }
                    },
                    "pct_biblioteca": {
                        "$avg": {
                            "$cond": [
                                {"$eq": ["$infraestrutura.possuiBiblioteca", True]},
                                100,
                                0,
                            ]
                        }
                    },
                    "pct_lab_informatica": {
                        "$avg": {
                            "$cond": [
                                {"$eq": ["$infraestrutura.possuiLabInformatica", True]},
                                100,
                                0,
                            ]
                        }
                    },
                    "pct_lab_ciencias": {
                        "$avg": {
                            "$cond": [
                                {"$eq": ["$infraestrutura.possuiLabCiencias", True]},
                                100,
                                0,
                            ]
                        }
                    },
                    "pct_quadra": {
                        "$avg": {
                            "$cond": [
                                {"$eq": ["$infraestrutura.possuiQuadraEsportes", True]},
                                100,
                                0,
                            ]
                        }
                    },
                    "pct_acessibilidade": {
                        "$avg": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$infraestrutura.possuiAcessibilidadePcd",
                                        True,
                                    ]
                                },
                                100,
                                0,
                            ]
                        }
                    },
                    "pct_agua_potavel": {
                        "$avg": {
                            "$cond": [
                                {"$eq": ["$infraestrutura.possuiAguaPotavel", True]},
                                100,
                                0,
                            ]
                        }
                    },
                    "escolas_por_dependencia": {"$push": "$dependenciaAdm"},
                    "escolas_por_zona": {"$push": "$tipoLocalizacao"},
                    "total_matriculas_infantil": {
                        "$sum": {"$ifNull": ["$matriculas.educacaoInfantil", 0]}
                    },
                    "total_matriculas_fundamental": {
                        "$sum": {"$ifNull": ["$matriculas.fundamentalTotal", 0]}
                    },
                    "total_matriculas_medio": {
                        "$sum": {"$ifNull": ["$matriculas.ensinoMedio", 0]}
                    },
                    "total_matriculas_eja": {
                        "$sum": {"$ifNull": ["$matriculas.eja", 0]}
                    },
                }
            },
        ]

        cursor = self._escolas.aggregate(pipeline)
        results = await cursor.to_list(length=1)

        if not results:
            return {}

        r = results[0]

        dependencias: dict[str, int] = {}
        for dep in r.get("escolas_por_dependencia", []):
            if dep:
                dependencias[dep] = dependencias.get(dep, 0) + 1

        zonas: dict[str, int] = {}
        for zona in r.get("escolas_por_zona", []):
            if zona:
                zonas[zona] = zonas.get(zona, 0) + 1

        matriculas_etapa = {}
        if r.get("total_matriculas_infantil", 0) > 0:
            matriculas_etapa["Educação Infantil"] = r.get(
                "total_matriculas_infantil", 0
            )
        if r.get("total_matriculas_fundamental", 0) > 0:
            matriculas_etapa["Ensino Fundamental"] = r.get(
                "total_matriculas_fundamental", 0
            )
        if r.get("total_matriculas_medio", 0) > 0:
            matriculas_etapa["Ensino Médio"] = r.get("total_matriculas_medio", 0)
        if r.get("total_matriculas_eja", 0) > 0:
            matriculas_etapa["EJA"] = r.get("total_matriculas_eja", 0)

        return {
            "total_escolas": r.get("total_escolas", 0),
            "total_alunos": r.get("total_alunos", 0),
            "taxa_aprovacao_media": r.get("avg_taxa_aprovacao"),
            "taxa_reprovacao_media": r.get("avg_taxa_reprovacao"),
            "avg_ideb_iniciais": r.get("avg_ideb_iniciais"),
            "avg_ideb_finais": r.get("avg_ideb_finais"),
            "pct_internet": r.get("pct_internet"),
            "pct_biblioteca": r.get("pct_biblioteca"),
            "pct_lab_informatica": r.get("pct_lab_informatica"),
            "pct_lab_ciencias": r.get("pct_lab_ciencias"),
            "pct_quadra": r.get("pct_quadra"),
            "pct_acessibilidade": r.get("pct_acessibilidade"),
            "pct_agua_potavel": r.get("pct_agua_potavel"),
            "por_dependencia": dependencias,
            "por_zona": zonas,
            "matriculas_por_etapa": matriculas_etapa,
        }

    async def _get_top_escolas(
        self,
        municipio_id_ibge: str,
        municipio_nome: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        match_conditions = self._municipio_match(municipio_id_ibge)
        match_conditions["ideb"] = {"$exists": True, "$ne": None}

        pipeline = [
            {"$match": match_conditions},
            {"$sort": {"ideb.anosIniciais": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "escolaNome": 1,
                    "escola_nome": 1,
                    "ideb": {"$ifNull": ["$ideb.anosIniciais", 0]},
                    "dependenciaAdm": 1,
                    "dependencia_adm": 1,
                    "tipoLocalizacao": 1,
                    "tipo_localizacao": 1,
                }
            },
        ]

        cursor = self._escolas.aggregate(pipeline)
        return await cursor.to_list(length=limit)

    def _municipio_match(self, municipio_id_ibge: str) -> dict[str, Any]:
        candidates = self._id_candidates(municipio_id_ibge)
        return {
            "$or": [
                {"municipioIdIbge": {"$in": candidates}},
                {"municipio_id_ibge": {"$in": candidates}},
            ]
        }

    @staticmethod
    def _id_candidates(municipio_id_ibge: str) -> list[Any]:
        candidates: list[Any] = [municipio_id_ibge]
        if municipio_id_ibge.isdigit():
            candidates.append(int(municipio_id_ibge))
        return candidates

    async def get_state_dossier_data(
        self,
        sg_uf: str,
    ) -> StateDossierData | None:
        uf = sg_uf.upper()

        total_municipios = await self._municipios.count_documents(
            {
                "$or": [
                    {"sg_uf": uf},
                    {"uf": uf},
                    {"estado_sigla": uf},
                    {"estadoSigla": uf},
                ]
            }
        )

        if total_municipios == 0:
            logger.warning("No data found for UF %s", uf)
            return None

        estado_nome = self._uf_to_name(uf)

        escolas_data = await self._aggregate_escolas_por_estado(uf)

        top_municipios = await self._get_top_municipios_por_ideb(uf, limit=10)

        infraestrutura = {}
        for key, aggr_key in [
            ("Internet", "pct_internet"),
            ("Biblioteca", "pct_biblioteca"),
            ("Lab. Informática", "pct_lab_informatica"),
            ("Acessibilidade PcD", "pct_acessibilidade"),
        ]:
            val = escolas_data.get(aggr_key)
            if val is not None:
                infraestrutura[key] = float(val)

        ideb_por_etapa = {}
        ideb_iniciais = escolas_data.get("avg_ideb_iniciais")
        ideb_finais = escolas_data.get("avg_ideb_finais")
        if ideb_iniciais is not None:
            ideb_por_etapa["Anos Iniciais"] = float(ideb_iniciais)
        if ideb_finais is not None:
            ideb_por_etapa["Anos Finais"] = float(ideb_finais)

        aprovacao_por_etapa = {}
        aprov_media = escolas_data.get("taxa_aprovacao_media")
        if aprov_media is not None:
            aprovacao_por_etapa["Anos Iniciais"] = float(aprov_media)
            aprovacao_por_etapa["Anos Finais"] = float(aprov_media)

        abandono_por_etapa: dict[str, float] = {}

        return StateDossierData(
            uf=uf,
            estado_nome=estado_nome,
            total_municipios=total_municipios,
            total_escolas=escolas_data.get("total_escolas", 0),
            total_alunos=escolas_data.get("total_alunos", 0),
            ideb_por_etapa=ideb_por_etapa,
            aprovacao_por_etapa=aprovacao_por_etapa,
            abandono_por_etapa=abandono_por_etapa,
            infraestrutura=infraestrutura,
            taxa_aprovacao_media=escolas_data.get("taxa_aprovacao_media"),
            taxa_reprovacao_media=escolas_data.get("taxa_reprovacao_media"),
            ideb_medio=escolas_data.get("ideb_medio"),
            pct_internet=escolas_data.get("pct_internet"),
            pct_biblioteca=escolas_data.get("pct_biblioteca"),
            pct_lab_informatica=escolas_data.get("pct_lab_informatica"),
            pct_acessibilidade=escolas_data.get("pct_acessibilidade"),
            escolas_por_dependencia=escolas_data.get("por_dependencia", {}),
            escolas_por_zona=escolas_data.get("por_zona", {}),
            top_municipios=top_municipios,
            indicadores_indisponiveis=[],
        )

    async def _aggregate_escolas_por_estado(self, sg_uf: str) -> dict[str, Any]:
        match_conditions = {
            "$or": [
                {"estadoSigla": sg_uf},
                {"estado_sigla": sg_uf},
                {"sg_uf": sg_uf},
                {"uf": sg_uf},
            ]
        }

        pipeline = [
            {"$match": match_conditions},
            {
                "$group": {
                    "_id": None,
                    "total_escolas": {"$sum": 1},
                    "total_alunos": {
                        "$sum": {"$ifNull": ["$matriculas.totalAlunos", 0]}
                    },
                    "avg_taxa_aprovacao": {
                        "$avg": {
                            "$avg": [
                                {
                                    "$ifNull": [
                                        "$indicadores.fundamentalAnosIniciais.taxaAprovacao",
                                        0,
                                    ]
                                },
                                {
                                    "$ifNull": [
                                        "$indicadores.fundamentalAnosFinais.taxaAprovacao",
                                        0,
                                    ]
                                },
                            ]
                        }
                    },
                    "avg_taxa_reprovacao": {
                        "$avg": {
                            "$avg": [
                                {
                                    "$ifNull": [
                                        "$indicadores.fundamentalAnosIniciais.taxaReprovacao",
                                        0,
                                    ]
                                },
                                {
                                    "$ifNull": [
                                        "$indicadores.fundamentalAnosFinais.taxaReprovacao",
                                        0,
                                    ]
                                },
                            ]
                        }
                    },
                    "avg_ideb_iniciais": {"$avg": "$ideb.anosIniciais"},
                    "avg_ideb_finais": {"$avg": "$ideb.anosFinais"},
                    "pct_internet": {
                        "$avg": {
                            "$cond": [
                                {"$eq": ["$infraestrutura.possuiInternet", True]},
                                100,
                                0,
                            ]
                        }
                    },
                    "pct_biblioteca": {
                        "$avg": {
                            "$cond": [
                                {"$eq": ["$infraestrutura.possuiBiblioteca", True]},
                                100,
                                0,
                            ]
                        }
                    },
                    "pct_lab_informatica": {
                        "$avg": {
                            "$cond": [
                                {"$eq": ["$infraestrutura.possuiLabInformatica", True]},
                                100,
                                0,
                            ]
                        }
                    },
                    "pct_acessibilidade": {
                        "$avg": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$infraestrutura.possuiAcessibilidadePcd",
                                        True,
                                    ]
                                },
                                100,
                                0,
                            ]
                        }
                    },
                    "escolas_por_dependencia": {"$push": "$dependenciaAdm"},
                    "escolas_por_zona": {"$push": "$tipoLocalizacao"},
                }
            },
        ]

        cursor = self._escolas.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        if not results:
            return {}

        r = results[0]
        dependencias: dict[str, int] = {}
        for dep in r.get("escolas_por_dependencia", []):
            if dep:
                dependencias[dep] = dependencias.get(dep, 0) + 1

        zonas: dict[str, int] = {}
        for zona in r.get("escolas_por_zona", []):
            if zona:
                zonas[zona] = zonas.get(zona, 0) + 1

        return {
            "total_escolas": r.get("total_escolas", 0),
            "total_alunos": r.get("total_alunos", 0),
            "taxa_aprovacao_media": r.get("avg_taxa_aprovacao"),
            "taxa_reprovacao_media": r.get("avg_taxa_reprovacao"),
            "avg_ideb_iniciais": r.get("avg_ideb_iniciais"),
            "avg_ideb_finais": r.get("avg_ideb_finais"),
            "pct_internet": r.get("pct_internet"),
            "pct_biblioteca": r.get("pct_biblioteca"),
            "pct_lab_informatica": r.get("pct_lab_informatica"),
            "pct_acessibilidade": r.get("pct_acessibilidade"),
            "por_dependencia": dependencias,
            "por_zona": zonas,
        }

    async def _get_top_municipios_por_ideb(
        self,
        sg_uf: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        match_conditions = {
            "$and": [
                {
                    "$or": [
                        {"sg_uf": sg_uf},
                        {"uf": sg_uf},
                        {"estado_sigla": sg_uf},
                        {"estadoSigla": sg_uf},
                    ]
                },
                {
                    "$or": [
                        {
                            "educacao.mediaIdebAnosIniciais": {
                                "$exists": True,
                                "$ne": None,
                            }
                        },
                        {"mediaIdebAnosIniciais": {"$exists": True, "$ne": None}},
                    ]
                },
            ]
        }

        pipeline = [
            {"$match": match_conditions},
            {"$sort": {"educacao.mediaIdebAnosIniciais": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "municipio": 1,
                    "nm_municipio": 1,
                    "municipio_nome": 1,
                    "ideb": {
                        "$ifNull": [
                            "$educacao.mediaIdebAnosIniciais",
                            "$mediaIdebAnosIniciais",
                            0,
                        ]
                    },
                    "total_escolas": {
                        "$ifNull": [
                            "$educacao.totalEscolas",
                            "$totalEscolas",
                            0,
                        ]
                    },
                    "total_matriculas": {
                        "$ifNull": [
                            "$educacao.totalMatriculas",
                            "$totalMatriculas",
                            0,
                        ]
                    },
                }
            },
        ]

        cursor = self._municipios.aggregate(pipeline)
        results = await cursor.to_list(length=limit)

        top_list = []
        for m in results:
            top_list.append(
                {
                    "nome": m.get("municipio")
                    or m.get("nm_municipio")
                    or m.get("municipio_nome")
                    or "",
                    "ideb": m.get("ideb") or 0,
                    "total_escolas": m.get("total_escolas") or 0,
                    "total_matriculas": m.get("total_matriculas") or 0,
                }
            )

        return top_list

    @staticmethod
    def _uf_to_name(sg_uf: str) -> str:
        names = {
            "AC": "Acre",
            "AL": "Alagoas",
            "AP": "Amapá",
            "AM": "Amazonas",
            "BA": "Bahia",
            "CE": "Ceará",
            "DF": "Distrito Federal",
            "ES": "Espírito Santo",
            "GO": "Goiás",
            "MA": "Maranhão",
            "MT": "Mato Grosso",
            "MS": "Mato Grosso do Sul",
            "MG": "Minas Gerais",
            "PA": "Pará",
            "PB": "Paraíba",
            "PR": "Paraná",
            "PE": "Pernambuco",
            "PI": "Piauí",
            "RJ": "Rio de Janeiro",
            "RN": "Rio Grande do Norte",
            "RS": "Rio Grande do Sul",
            "RO": "Rondônia",
            "RR": "Roraima",
            "SC": "Santa Catarina",
            "SP": "São Paulo",
            "SE": "Sergipe",
            "TO": "Tocantins",
        }
        return names.get(sg_uf.upper(), sg_uf.upper())

    @staticmethod
    def _avg(*values: Any) -> float | None:
        nums = [float(v) for v in values if v is not None]
        if not nums:
            return None
        return sum(nums) / len(nums)

    @staticmethod
    def _complement(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return round(100 - float(value), 1)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
