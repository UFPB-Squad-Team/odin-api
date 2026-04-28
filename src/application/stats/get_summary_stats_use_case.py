from src.domain.entities.stats import SummaryStats
from src.domain.repository.stats_repository import IStatsRepository

class GetSummaryStatsUseCase:
    def __init__(self, repository: IStatsRepository):
        self.repository = repository

    async def execute(self) -> SummaryStats:
        """
        Coordena a obtenção das estatísticas agregadas e aplica a regra de negócio
        (cálculo de percentuais e formatação final dos indicadores).
        """
        # 1. Busca os dados "crus" no repositório
        data = await self.repository.get_summary_stats()
        
        if not data:
            return SummaryStats(
                total_escolas=0, total_municipios=0, 
                indicadores_infra={}, por_dependencia={}, por_zona={}
            )

        # 2. Aplica as regras de negócio
        totais = data.get("totais", [{}])[0] if data.get("totais") else {}
        total_escolas = totais.get("total_escolas", 0)
        
        def calc_pct(qtd, total):
            return round((qtd / total * 100), 2) if total > 0 else 0.0

        indicadores_infra = {
            "Internet (%)": calc_pct(totais.get("qtd_internet", 0), total_escolas),
            "Biblioteca (%)": calc_pct(totais.get("qtd_biblioteca", 0), total_escolas),
            "Lab. Informática (%)": calc_pct(totais.get("qtd_informatica", 0), total_escolas)
        }

        por_dependencia = {
            item["_id"]: item["count"] for item in data.get("dependencia", []) if item.get("_id")
        }
        
        por_zona = {
            item["_id"]: item["count"] for item in data.get("zona", []) if item.get("_id")
        }
        
        total_municipios = len(data.get("municipios", []))
        
        # 3. Retorna a Entidade perfeitamente formatada para o Controller
        return SummaryStats(
            total_escolas=total_escolas,
            total_municipios=total_municipios,
            indicadores_infra=indicadores_infra,
            por_dependencia=por_dependencia,
            por_zona=por_zona
        )