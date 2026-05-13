from src.domain.entities.state_summary import (
    StateSummary, 
    EducacaoStateStats, 
    SocioeconomicoStateStats
)
from src.domain.repository.state_repository import IStateRepository

class GetStateSummaryUseCase:
    def __init__(self, state_repository: IStateRepository):
        self.state_repository = state_repository

    def _get_number(self, data: dict, key: str) -> float:
        """Extrai o número de forma segura lidando com dicionários e valores nulos."""
        val = data.get(key, 0)
        if isinstance(val, dict):
            return float(val.get("total", val.get("valor", 0)))
        return float(val) if val is not None else 0.0

    def _round_safe(self, value: float | None, decimals: int = 2) -> float | None:
        """Arredonda o valor com segurança."""
        return round(value, decimals) if value is not None else None

    async def execute(self, sg_uf: str) -> StateSummary | None:
        cities = await self.state_repository.get_cities_data_by_state(sg_uf)
        if not cities:
            return None 

        
        total_escolas = 0
        total_alunos = 0
        escolas_com_biblioteca = 0
        escolas_com_internet = 0
        escolas_com_lab = 0
        escolas_sem_acessibilidade = 0
        
        
        soma_ponderada_ideb_iniciais = 0
        soma_ponderada_ideb_finais = 0
        alunos_com_ideb_iniciais = 0
        alunos_com_ideb_finais = 0

        
        populacao_total = 0
        soma_ponderada_desemprego = 0 

        for city in cities:
            educacao = city.get("educacao") or {}
            socio = city.get("socioeconomico") or {}

            
            qtd_escolas = self._get_number(educacao, "totalEscolas")
            qtd_alunos = self._get_number(educacao, "totalMatriculas")
            
            total_escolas += qtd_escolas
            total_alunos += qtd_alunos

            if qtd_escolas > 0:
                escolas_com_biblioteca += (qtd_escolas * self._get_number(educacao, "pctComBiblioteca"))
                escolas_com_internet += (qtd_escolas * self._get_number(educacao, "pctComInternet"))
                escolas_com_lab += (qtd_escolas * self._get_number(educacao, "pctComLabInformatica"))
                escolas_sem_acessibilidade += (qtd_escolas * self._get_number(educacao, "pctSemAcessibilidade"))

            
            ideb_iniciais = self._get_number(educacao, "mediaIdebAnosIniciais")
            ideb_finais = self._get_number(educacao, "mediaIdebAnosFinals")

            if ideb_iniciais > 0:
                soma_ponderada_ideb_iniciais += (ideb_iniciais * qtd_alunos)
                alunos_com_ideb_iniciais += qtd_alunos
            
            if ideb_finais > 0:
                soma_ponderada_ideb_finais += (ideb_finais * qtd_alunos)
                alunos_com_ideb_finais += qtd_alunos

            
            pop_cidade = self._get_number(socio, "populacao")
            populacao_total += pop_cidade

            if pop_cidade > 0:
                taxa_desemprego_cidade = self._get_number(socio, "taxaDesemprego")
                soma_ponderada_desemprego += (taxa_desemprego_cidade * pop_cidade)

        
        avg_ideb_iniciais = (soma_ponderada_ideb_iniciais / alunos_com_ideb_iniciais) if alunos_com_ideb_iniciais > 0 else None
        avg_ideb_finais = (soma_ponderada_ideb_finais / alunos_com_ideb_finais) if alunos_com_ideb_finais > 0 else None
        
        taxa_desemprego_estado = (soma_ponderada_desemprego / populacao_total) if populacao_total > 0 else None

        return StateSummary(
            sg_uf=sg_uf.upper(),
            educacao=EducacaoStateStats(
                total_escolas=int(total_escolas),
                total_alunos=int(total_alunos),
                pct_com_biblioteca=self._round_safe( (escolas_com_biblioteca / total_escolas) if total_escolas > 0 else 0 ),
                pct_com_internet=self._round_safe( (escolas_com_internet / total_escolas) if total_escolas > 0 else 0 ),
                pct_com_lab_informatica=self._round_safe( (escolas_com_lab / total_escolas) if total_escolas > 0 else 0 ),
                pct_sem_acessibilidade=self._round_safe( (escolas_sem_acessibilidade / total_escolas) if total_escolas > 0 else 0 ),
                avg_ideb_iniciais=self._round_safe(avg_ideb_iniciais),
                avg_ideb_finais=self._round_safe(avg_ideb_finais)
            ),
            socioeconomico=SocioeconomicoStateStats(
                populacao_total=int(populacao_total),
                indicadores={
                    "taxa_desemprego_media": self._round_safe(taxa_desemprego_estado)
                }
            )
        )