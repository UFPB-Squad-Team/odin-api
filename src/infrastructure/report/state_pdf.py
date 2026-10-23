"""Synchronous state dossier rendering, imported only on the PDF thread."""


def render_state_dossier(state_data):
    # Build a municipio-like data structure for the PDF generator
    # (reusing the same DossierPDF class with adapted data)
    from src.domain.entities.report import MunicipioDossierData
    from src.infrastructure.report.chart_generator import (
        generate_bar_chart,
        generate_horizontal_bar_chart,
        generate_pie_chart,
    )
    from src.infrastructure.report.pdf_generator import DossierPDF

    adapted_data = MunicipioDossierData(
        municipio_id=state_data.uf,
        municipio_nome=state_data.estado_nome,
        uf=state_data.uf,
        total_escolas=state_data.total_escolas,
        total_alunos=state_data.total_alunos,
        total_bairros=state_data.total_municipios,
        ideb_por_etapa=state_data.ideb_por_etapa,
        aprovacao_por_etapa=state_data.aprovacao_por_etapa,
        escolas_por_dependencia=state_data.escolas_por_dependencia,
        escolas_por_zona=state_data.escolas_por_zona,
        top_escolas=[
            {
                "nome": m["nome"],
                "ideb": m["ideb"],
                "dependencia": "",
                "localizacao": "",
            }
            for m in state_data.top_municipios
        ],
    )

    pdf = DossierPDF(adapted_data)

    # Generate charts
    infra_labels, infra_values = [], []
    for label, val in [
        ("Internet", state_data.pct_internet),
        ("Biblioteca", state_data.pct_biblioteca),
        ("Lab. Informática", state_data.pct_lab_informatica),
        ("Acessibilidade", state_data.pct_acessibilidade),
    ]:
        if val is not None:
            infra_labels.append(label)
            infra_values.append(val)

    if infra_labels:
        chart = generate_bar_chart(
            labels=infra_labels,
            values=infra_values,
            title="Infraestrutura Escolar",
            ylabel="Percentual de Escolas (%)",
        )
        pdf.add_chart("infra_bars", chart)

    if state_data.escolas_por_dependencia:
        dep_labels = list(state_data.escolas_por_dependencia.keys())
        dep_values = [float(v) for v in state_data.escolas_por_dependencia.values()]
        chart = generate_pie_chart(
            labels=dep_labels,
            values=dep_values,
            title="Dependência Administrativa",
        )
        pdf.add_chart("dependencia_pie", chart)

    if state_data.escolas_por_zona:
        zona_labels = list(state_data.escolas_por_zona.keys())
        zona_values = [float(v) for v in state_data.escolas_por_zona.values()]
        chart = generate_pie_chart(
            labels=zona_labels,
            values=zona_values,
            title="Localização (Urbana/Rural)",
        )
        pdf.add_chart("zona_pie", chart)

    if state_data.top_municipios:
        city_names = [
            m["nome"][:25] + ("..." if len(m["nome"]) > 25 else "")
            for m in state_data.top_municipios
        ]
        city_idebs = [float(m["ideb"]) for m in state_data.top_municipios]
        chart = generate_horizontal_bar_chart(
            labels=city_names,
            values=city_idebs,
            title="Top Municípios — IDEB",
            xlabel="IDEB",
        )
        pdf.add_chart("top_schools", chart)

    pdf_stream = pdf.render()
    return pdf_stream
