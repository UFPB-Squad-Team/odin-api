from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import HRFlowable

from src.domain.entities.report import MunicipioDossierData, StateDossierData

ODIN_BLUE = "#1A5276"
ODIN_DARK_BLUE = "#0E2F44"
ODIN_GREEN = "#1E8449"
ODIN_RED = "#C0392B"
ODIN_ORANGE = "#E67E22"
ODIN_LIGHT_GRAY = "#F4F6F7"
ODIN_MEDIUM_GRAY = "#D5D8DC"
ODIN_TEXT = "#1C2833"
ODIN_MUTED = "#6C757D"
ODIN_WHITE_MUTED = "#C7D6DE"
ODIN_GOLD = "#F1C40F"
ODIN_TEAL = "#148F77"
ODIN_PURPLE = "#6C3483"

PAGE_W, PAGE_H = A4
MARGIN_LEFT = 1.8 * cm
MARGIN_RIGHT = 1.8 * cm
MARGIN_TOP = 1.6 * cm
MARGIN_BOTTOM = 1.6 * cm
CONTENT_W = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT

_MESES_PT = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}


def _data_por_extenso(dt: datetime) -> str:
    return f"{dt.day:02d} de {_MESES_PT[dt.month]} de {dt.year}"


def _mpl_style():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.linestyle": "--",
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.titlecolor": ODIN_DARK_BLUE,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
        }
    )


def _fig_to_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    plt.close(fig)
    return buf.read()


def _chart_image(chart_bytes: bytes, width_cm: float, height_cm: float) -> Image:
    img = Image(io.BytesIO(chart_bytes))
    img.drawWidth = width_cm * cm
    img.drawHeight = height_cm * cm
    return img


def _build_styles() -> dict:
    return {
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            fontName="Helvetica-Bold",
            fontSize=30,
            leading=36,
            textColor=colors.white,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "CoverEntity": ParagraphStyle(
            "CoverEntity",
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            textColor=colors.HexColor(ODIN_GREEN),
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            fontName="Helvetica-Oblique",
            fontSize=12,
            leading=17,
            textColor=colors.HexColor(ODIN_WHITE_MUTED),
            alignment=TA_CENTER,
        ),
        "CoverDate": ParagraphStyle(
            "CoverDate",
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor(ODIN_WHITE_MUTED),
            alignment=TA_CENTER,
        ),
        "SectionTitle": ParagraphStyle(
            "SectionTitle",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.white,
        ),
        "SubSectionTitle": ParagraphStyle(
            "SubSectionTitle",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor(ODIN_DARK_BLUE),
            spaceBefore=10,
            spaceAfter=5,
        ),
        "BodyText": ParagraphStyle(
            "BodyText",
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor(ODIN_TEXT),
            alignment=TA_JUSTIFY,
            spaceBefore=2,
            spaceAfter=5,
        ),
        "BodyBold": ParagraphStyle(
            "BodyBold",
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor(ODIN_TEXT),
        ),
        "ValueText": ParagraphStyle(
            "ValueText",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor(ODIN_DARK_BLUE),
            alignment=TA_CENTER,
        ),
        "LabelText": ParagraphStyle(
            "LabelText",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor(ODIN_MUTED),
            alignment=TA_CENTER,
        ),
        "CaptionText": ParagraphStyle(
            "CaptionText",
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor(ODIN_MUTED),
            alignment=TA_CENTER,
            spaceBefore=2,
            spaceAfter=6,
        ),
        "SmallMuted": ParagraphStyle(
            "SmallMuted",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor(ODIN_MUTED),
        ),
        "AnalysisBox": ParagraphStyle(
            "AnalysisBox",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor(ODIN_DARK_BLUE),
            alignment=TA_JUSTIFY,
            spaceBefore=0,
            spaceAfter=0,
            leftIndent=8,
            rightIndent=8,
        ),
        "BulletText": ParagraphStyle(
            "BulletText",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor(ODIN_TEXT),
            leftIndent=12,
            spaceBefore=1,
            spaceAfter=1,
        ),
    }


def _header_footer(canvas, doc):
    canvas.saveState()
    if doc.page == 1:
        canvas.setFillColor(colors.HexColor(ODIN_DARK_BLUE))
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        for i, (color, alpha) in enumerate(
            [(ODIN_BLUE, 0.25), (ODIN_TEAL, 0.15), (ODIN_GREEN, 0.1)]
        ):
            r = (8 - i * 2) * cm
            cx, cy = PAGE_W * 0.12, PAGE_H * 0.85
            canvas.setFillColor(colors.HexColor(color))
            canvas.setFillAlpha(alpha)
            canvas.circle(cx, cy, r, fill=1, stroke=0)
        canvas.setFillAlpha(1)
        for i, (color, alpha) in enumerate([(ODIN_GREEN, 0.2), (ODIN_TEAL, 0.12)]):
            r = (6 - i * 2) * cm
            canvas.setFillColor(colors.HexColor(color))
            canvas.setFillAlpha(alpha)
            canvas.circle(PAGE_W * 0.9, PAGE_H * 0.2, r, fill=1, stroke=0)
        canvas.setFillAlpha(1)
        stripe_h = 0.45 * cm
        stripe_y = 2.8 * cm
        canvas.setFillColor(colors.HexColor(ODIN_GREEN))
        canvas.rect(0, stripe_y, PAGE_W * 0.55, stripe_h, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor(ODIN_ORANGE))
        canvas.rect(PAGE_W * 0.55, stripe_y, PAGE_W * 0.45, stripe_h, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor(ODIN_WHITE_MUTED))
        canvas.setFont("Helvetica", 8.5)
        canvas.drawCentredString(
            PAGE_W / 2,
            1.9 * cm,
            "Observatório de Dados Integrados do Nordeste — LEMA/UFPB",
        )
        canvas.restoreState()
        return

    canvas.setFillColor(colors.HexColor(ODIN_BLUE))
    canvas.rect(0, PAGE_H - 0.9 * cm, PAGE_W, 0.9 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(
        MARGIN_LEFT,
        PAGE_H - 0.6 * cm,
        "ODIN — Observatório de Dados Integrados do Nordeste  |  LEMA/UFPB",
    )
    canvas.drawRightString(PAGE_W - MARGIN_RIGHT, PAGE_H - 0.6 * cm, f"{doc._title}")

    canvas.setFillColor(colors.HexColor(ODIN_LIGHT_GRAY))
    canvas.rect(0, 0, PAGE_W, 0.85 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor(ODIN_MUTED))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(
        MARGIN_LEFT,
        0.28 * cm,
        "ODIN — Observatório de Dados Integrados do Nordeste | LEMA/UFPB",
    )
    canvas.drawRightString(PAGE_W - MARGIN_RIGHT, 0.28 * cm, f"Página {doc.page}")
    canvas.setStrokeColor(colors.HexColor(ODIN_MEDIUM_GRAY))
    canvas.setLineWidth(0.4)
    canvas.line(0, 0.85 * cm, PAGE_W, 0.85 * cm)
    canvas.restoreState()


def _section_header(title: str, icon: str = "●") -> Table:
    s = _build_styles()
    t = Table(
        [[Paragraph(f"{icon}  {title}", s["SectionTitle"])]], colWidths=[CONTENT_W]
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(ODIN_BLUE)),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("ROUNDEDCORNERS", [4, 4, 4, 4]),
            ]
        )
    )
    return t


def _analysis_box(text: str) -> Table:
    s = _build_styles()
    t = Table([[Paragraph(text, s["AnalysisBox"])]], colWidths=[CONTENT_W])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EBF5FB")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LINEONSIDES", (0, 0), (0, -1), 3, colors.HexColor(ODIN_BLUE)),
            ]
        )
    )
    return t


def _kpi_card(label: str, value: str, color: str = ODIN_BLUE) -> Table:
    s = _build_styles()
    rows = [
        [Paragraph(f'<font color="{color}"><b>{value}</b></font>', s["ValueText"])],
        [Paragraph(label, s["LabelText"])],
    ]
    w = (CONTENT_W - 4 * 3) / 4
    t = Table(rows, colWidths=[w])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(ODIN_MEDIUM_GRAY)),
                ("LINEABOVE", (0, 0), (-1, 0), 3, colors.HexColor(color)),
            ]
        )
    )
    return t


def _kpi_row(cards: list) -> Table:
    w = (CONTENT_W - 3 * 4) / len(cards)
    t = Table([cards], colWidths=[w] * len(cards))
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return t


def _standard_table(
    header: list, rows: list, col_widths: list, alt_rows: bool = True
) -> Table:
    all_data = [header] + rows
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(ODIN_BLUE)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor(ODIN_DARK_BLUE)),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor(ODIN_MEDIUM_GRAY)),
    ]
    if alt_rows:
        for i in range(1, len(all_data)):
            if i % 2 == 0:
                style.append(
                    ("BACKGROUND", (0, i), (-1, i), colors.HexColor(ODIN_LIGHT_GRAY))
                )
    t = Table(all_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(style))
    return t


def _ideb_colored(val: float | None) -> str:
    if val is None:
        return "<font color='#6C757D'>—</font>"
    c = ODIN_GREEN if val >= 6.0 else (ODIN_ORANGE if val >= 4.5 else ODIN_RED)
    return f'<font color="{c}"><b>{val:.2f}</b></font>'


def _pct_colored(val: float | None, threshold_good=80, threshold_warn=60) -> str:
    if val is None:
        return "<font color='#6C757D'>—</font>"
    c = (
        ODIN_GREEN
        if val >= threshold_good
        else (ODIN_ORANGE if val >= threshold_warn else ODIN_RED)
    )
    return f'<font color="{c}"><b>{val:.1f}%</b></font>'


class DossierPDF:
    def __init__(self, data: MunicipioDossierData) -> None:
        self.data = data
        self.styles = _build_styles()
        self._story: list[Any] = []
        self._charts: dict[str, bytes] = {}
        self._title = f"{data.municipio_nome} / {data.uf}"

    def add_chart(self, key: str, chart_bytes: bytes) -> None:
        self._charts[key] = chart_bytes

    def _has_any_data(self) -> bool:
        d = self.data
        return (
            d.total_escolas > 0
            or d.total_alunos > 0
            or d.ideb_por_etapa
            or d.aprovacao_por_etapa
            or d.infraestrutura
            or d.escolas_por_dependencia
            or d.saneamento
            or d.habitacao
            or d.estrutura_etaria
            or d.raca
            or d.genero
        )

    def _generate_charts(self):
        d = self.data
        if not self._has_any_data():
            return

        ideb_etapas = list(d.ideb_por_etapa.keys())
        aprov_etapas = list(d.aprovacao_por_etapa.keys())

        if ideb_etapas and aprov_etapas:
            fig = self._chart_ideb_grouped()
            self.add_chart("ideb_grouped", fig)
        if ideb_etapas and any(d.abandono_por_etapa.values()):
            fig = self._chart_abandono_distorcao()
            self.add_chart("abandono_distorcao", fig)
        if d.infraestrutura:
            fig = self._chart_infraestrutura()
            self.add_chart("infra_bars", fig)
        # Removed matrículas chart because data may be unreliable
        if d.escolas_por_dependencia or d.escolas_por_zona:
            fig = self._chart_dependencia_zona()
            self.add_chart("dependencia_zona", fig)
        if d.top_escolas:
            fig = self._chart_top_schools()
            self.add_chart("top_schools", fig)
        if d.estrutura_etaria or d.raca:
            fig = self._chart_estrutura_etaria()
            self.add_chart("estrutura_etaria", fig)
        if d.saneamento or d.habitacao:
            fig = self._chart_saneamento_habitacao()
            self.add_chart("saneamento_habitacao", fig)
        if (
            d.adequacao_docente_por_etapa
            or d.docentes_superior_por_etapa
            or d.alunos_por_turma_etapa
        ):
            fig = self._chart_docentes()
            self.add_chart("docentes", fig)

    def _chart_ideb_grouped(self) -> bytes:
        _mpl_style()
        d = self.data
        etapas = list(d.ideb_por_etapa.keys())
        ideb_vals = [d.ideb_por_etapa[e] for e in etapas]
        aprov_vals = [d.aprovacao_por_etapa.get(e, 0) / 10 for e in etapas]
        meta_nacional = 6.0

        x = np.arange(len(etapas))
        w = 0.35
        fig, ax = plt.subplots(figsize=(10, 5.0))

        bars1 = ax.bar(x - w / 2, ideb_vals, w, label="IDEB", color=ODIN_BLUE, zorder=3)
        bars2 = ax.bar(
            x + w / 2,
            aprov_vals,
            w,
            label="Aprovação/10",
            color=ODIN_TEAL,
            alpha=0.85,
            zorder=3,
        )
        ax.axhline(
            meta_nacional,
            color=ODIN_RED,
            linewidth=1.4,
            linestyle="--",
            label=f"Meta Nacional ({meta_nacional})",
        )

        for bar, val in zip(bars1, ideb_vals, strict=False):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                color=ODIN_BLUE,
            )
        for bar, val in zip(bars2, aprov_vals, strict=False):
            real_val = val * 10
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                f"{real_val:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8,
                color=ODIN_TEAL,
            )

        ax.set_xticks(x)
        ax.set_xticklabels(etapas, fontsize=9)
        ax.set_ylim(0, 11)
        ax.set_ylabel("Valor")
        ax.set_title("IDEB e Taxa de Aprovação por Etapa de Ensino")
        ax.legend(fontsize=8, loc="upper right")
        fig.tight_layout()
        return _fig_to_bytes(fig)

    def _chart_abandono_distorcao(self) -> bytes:
        _mpl_style()
        d = self.data
        etapas = list(d.abandono_por_etapa.keys())
        aband = [d.abandono_por_etapa.get(e, 0) for e in etapas]
        distor = [d.distorcao_idade_serie_por_etapa.get(e, 0) for e in etapas]

        x = np.arange(len(etapas))
        w = 0.35
        fig, ax = plt.subplots(figsize=(10, 4.8))

        b1 = ax.bar(
            x - w / 2,
            aband,
            w,
            label="Abandono (%)",
            color=ODIN_RED,
            alpha=0.85,
            zorder=3,
        )
        b2 = ax.bar(
            x + w / 2,
            distor,
            w,
            label="Distorção Idade-Série (%)",
            color=ODIN_ORANGE,
            alpha=0.85,
            zorder=3,
        )

        for bar, val in zip(b1, aband, strict=False):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.2,
                f"{val:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                color=ODIN_RED,
            )
        for bar, val in zip(b2, distor, strict=False):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.2,
                f"{val:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8,
                color=ODIN_ORANGE,
            )

        ax.set_xticks(x)
        ax.set_xticklabels(etapas, fontsize=9)
        ax.set_ylabel("Percentual (%)")
        ax.set_title("Abandono Escolar e Distorção Idade-Série por Etapa")
        ax.legend(fontsize=8)
        fig.tight_layout()
        return _fig_to_bytes(fig)

    def _chart_infraestrutura(self) -> bytes:
        _mpl_style()
        infra = self.data.infraestrutura
        if not infra:
            return b""
        labels = list(infra.keys())
        values = list(infra.values())
        sorted_pairs = sorted(zip(values, labels, strict=False), reverse=True)
        values, labels = zip(*sorted_pairs, strict=False)

        bar_colors = [
            ODIN_GREEN if v >= 70 else (ODIN_ORANGE if v >= 40 else ODIN_RED)
            for v in values
        ]

        fig, ax = plt.subplots(figsize=(10, 6.5))
        y = np.arange(len(labels))
        bars = ax.barh(
            y, values, color=bar_colors, edgecolor="white", linewidth=0.5, zorder=3
        )

        for bar, val in zip(bars, values, strict=False):
            ax.text(
                min(val + 1, 102),
                bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%",
                va="center",
                fontsize=8,
                fontweight="bold",
            )

        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlim(0, 112)
        ax.set_xlabel("Percentual de Escolas (%)")
        ax.set_title("Cobertura de Infraestrutura nas Escolas")
        ax.axvline(70, color=ODIN_MEDIUM_GRAY, linewidth=0.8, linestyle=":")

        legend_elements = [
            mpatches.Patch(color=ODIN_GREEN, label="≥ 70% (Adequado)"),
            mpatches.Patch(color=ODIN_ORANGE, label="40–69% (Atenção)"),
            mpatches.Patch(color=ODIN_RED, label="< 40% (Crítico)"),
        ]
        ax.legend(handles=legend_elements, fontsize=7, loc="lower right")
        fig.tight_layout()
        return _fig_to_bytes(fig)

    def _chart_dependencia_zona(self) -> bytes:
        _mpl_style()
        dep = self.data.escolas_por_dependencia
        zona = self.data.escolas_por_zona
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8))

        if dep:
            dep_labels = list(dep.keys())
            dep_vals = list(dep.values())
            dep_colors = [ODIN_BLUE, ODIN_GREEN, ODIN_TEAL]
            wedges, texts, autotexts = ax1.pie(
                dep_vals,
                labels=dep_labels,
                colors=dep_colors,
                autopct="%1.1f%%",
                startangle=90,
                pctdistance=0.75,
                wedgeprops={"edgecolor": "white", "linewidth": 2},
            )
            for t in texts:
                t.set_fontsize(9)
            for at in autotexts:
                at.set_fontsize(9)
                at.set_color("white")
                at.set_fontweight("bold")
            total_dep = sum(dep_vals)
            ax1.set_title(
                f"Dependência Administrativa\n({total_dep} escolas)", fontsize=10
            )
            for i, (val, label) in enumerate(zip(dep_vals, dep_labels, strict=False)):
                ax1.annotate(
                    f"{val} escolas",
                    xy=(0, -1.3 - i * 0.18),
                    ha="center",
                    fontsize=8,
                    color=dep_colors[i],
                )
        else:
            ax1.set_title("Dependência Administrativa\n(sem dados)", fontsize=10)
            ax1.text(
                0,
                0,
                "Não disponível",
                ha="center",
                va="center",
                fontsize=10,
                color=ODIN_MUTED,
            )
            ax1.set_aspect(1)

        if zona:
            zona_labels = list(zona.keys())
            zona_vals = list(zona.values())
            zona_colors = [
                ODIN_TEAL if z == "Urbana" else ODIN_ORANGE for z in zona_labels
            ]
            ax2.bar(zona_labels, zona_vals, color=zona_colors, width=0.4, zorder=3)
            for i, val in enumerate(zona_vals):
                ax2.text(
                    i,
                    val + 5,
                    f"{val} ({val/sum(zona_vals)*100:.1f}%)",
                    ha="center",
                    fontsize=9,
                    fontweight="bold",
                )
            ax2.set_ylim(0, max(zona_vals) * 1.15 if zona_vals else 10)
            ax2.set_title("Localização das Escolas", fontsize=10)
            ax2.set_ylabel("Número de Escolas")
        else:
            ax2.set_title("Localização das Escolas\n(sem dados)", fontsize=10)
            ax2.text(
                0.5,
                0.5,
                "Não disponível",
                ha="center",
                va="center",
                fontsize=10,
                color=ODIN_MUTED,
            )
            ax2.set_ylim(0, 1)
            ax2.set_yticks([])

        fig.tight_layout()
        return _fig_to_bytes(fig)

    def _chart_top_schools(self) -> bytes:
        _mpl_style()
        schools = self.data.top_escolas
        if not schools:
            return b""
        schools = schools[:10]
        names = [s["nome"] for s in schools]
        idebs = [s["ideb"] for s in schools]
        bar_colors = [
            ODIN_GOLD if v >= 6.5 else (ODIN_GREEN if v >= 6.0 else ODIN_TEAL)
            for v in idebs
        ]

        fig, ax = plt.subplots(figsize=(10, 5.5))
        y = np.arange(len(names))
        bars = ax.barh(
            y, idebs, color=bar_colors, edgecolor="white", linewidth=0.5, zorder=3
        )

        for bar, val in zip(bars, idebs, strict=False):
            ax.text(
                val + 0.03,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}",
                va="center",
                fontsize=9,
                fontweight="bold",
            )

        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=8.5)
        ax.set_xlim(0, max(idebs) + 0.8 if idebs else 10)
        ax.set_xlabel("IDEB (Anos Iniciais)")
        ax.set_title("Top 10 Escolas por IDEB — Anos Iniciais")

        media_ideb = None
        if "Anos Iniciais" in self.data.ideb_por_etapa:
            media_ideb = self.data.ideb_por_etapa["Anos Iniciais"]
        if media_ideb is not None:
            ax.axvline(
                media_ideb,
                color=ODIN_BLUE,
                linestyle="--",
                linewidth=1.2,
                label=f"Média municipal ({media_ideb:.2f})",
            )
        ax.axvline(
            6.0,
            color=ODIN_RED,
            linestyle=":",
            linewidth=1.0,
            label="Meta nacional (6.0)",
        )

        legend_elements = [
            mpatches.Patch(color=ODIN_GOLD, label="IDEB ≥ 6.5 (Excelente)"),
            mpatches.Patch(color=ODIN_GREEN, label="6.0–6.4 (Muito bom)"),
            mpatches.Patch(color=ODIN_TEAL, label="< 6.0 (Bom)"),
        ]
        extra = []
        if media_ideb is not None:
            extra.append(
                plt.Line2D(
                    [0],
                    [0],
                    color=ODIN_BLUE,
                    linestyle="--",
                    label=f"Média municipal ({media_ideb:.2f})",
                )
            )
        extra.append(
            plt.Line2D(
                [0], [0], color=ODIN_RED, linestyle=":", label="Meta nacional (6.0)"
            )
        )
        ax.legend(handles=legend_elements + extra, fontsize=7.5, loc="lower right")
        fig.tight_layout()
        return _fig_to_bytes(fig)

    def _chart_estrutura_etaria(self) -> bytes:
        _mpl_style()
        etaria = self.data.estrutura_etaria
        raca = self.data.raca

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8))

        if etaria:
            labels_e = list(etaria.keys())
            vals_e = list(etaria.values())
            colors_e = [ODIN_ORANGE, ODIN_TEAL, ODIN_BLUE, ODIN_PURPLE]
            wedges, texts, autotexts = ax1.pie(
                vals_e,
                labels=labels_e,
                colors=colors_e,
                autopct="%1.1f%%",
                startangle=120,
                pctdistance=0.78,
                wedgeprops={"edgecolor": "white", "linewidth": 1.5},
            )
            for t in texts:
                t.set_fontsize(8)
            for at in autotexts:
                at.set_fontsize(8)
                at.set_fontweight("bold")
                at.set_color("white")
            ax1.set_title("Estrutura Etária da População")
        else:
            ax1.set_title("Estrutura Etária\n(sem dados)", fontsize=10)
            ax1.text(
                0,
                0,
                "Não disponível",
                ha="center",
                va="center",
                fontsize=10,
                color=ODIN_MUTED,
            )
            ax1.set_aspect(1)

        if raca:
            labels_r = list(raca.keys())
            vals_r = list(raca.values())
            colors_r = [ODIN_DARK_BLUE, ODIN_TEAL, ODIN_ORANGE, ODIN_MEDIUM_GRAY]
            bars = ax2.bar(
                labels_r,
                vals_r,
                color=colors_r,
                edgecolor="white",
                linewidth=0.5,
                zorder=3,
            )
            for bar, val in zip(bars, vals_r, strict=False):
                ax2.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    f"{val:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=8.5,
                    fontweight="bold",
                )
            ax2.set_ylim(0, max(vals_r) * 1.15 if vals_r else 10)
            ax2.set_ylabel("Percentual (%)")
            ax2.set_title("Composição Racial")
        else:
            ax2.set_title("Composição Racial\n(sem dados)", fontsize=10)
            ax2.text(
                0.5,
                0.5,
                "Não disponível",
                ha="center",
                va="center",
                fontsize=10,
                color=ODIN_MUTED,
            )
            ax2.set_ylim(0, 1)
            ax2.set_yticks([])

        fig.tight_layout()
        return _fig_to_bytes(fig)

    def _chart_saneamento_habitacao(self) -> bytes:
        _mpl_style()
        san = self.data.saneamento
        hab = self.data.habitacao

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.0))

        if san:
            labels_s = list(san.keys())
            vals_s = list(san.values())
            bar_colors_s = [ODIN_GREEN if v >= 70 else ODIN_ORANGE for v in vals_s]
            x_s = np.arange(len(labels_s))
            bars_s = ax1.bar(x_s, vals_s, color=bar_colors_s, zorder=3)
            for bar, val in zip(bars_s, vals_s, strict=False):
                ax1.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.8,
                    f"{val:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=8.5,
                    fontweight="bold",
                )
            ax1.set_xticks(x_s)
            ax1.set_xticklabels(labels_s, fontsize=8.5)
            ax1.set_ylim(0, max(vals_s) * 1.15 if vals_s else 10)
            ax1.set_ylabel("Percentual de Domicílios (%)")
            ax1.set_title("Saneamento Básico")
            ax1.axhline(70, color=ODIN_MEDIUM_GRAY, linestyle=":", linewidth=0.8)
        else:
            ax1.set_title("Saneamento\n(sem dados)", fontsize=10)
            ax1.text(
                0.5,
                0.5,
                "Não disponível",
                ha="center",
                va="center",
                fontsize=10,
                color=ODIN_MUTED,
            )
            ax1.set_ylim(0, 1)
            ax1.set_yticks([])

        if hab:
            labels_h = list(hab.keys())
            vals_h = list(hab.values())
            bar_colors_h = [ODIN_BLUE, ODIN_TEAL, ODIN_PURPLE, ODIN_ORANGE]
            x_h = np.arange(len(labels_h))
            bars_h = ax2.bar(x_h, vals_h, color=bar_colors_h, zorder=3)
            for bar, val in zip(bars_h, vals_h, strict=False):
                ax2.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.3,
                    f"{val:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=8.5,
                    fontweight="bold",
                )
            ax2.set_xticks(x_h)
            ax2.set_xticklabels(labels_h, fontsize=7.5)
            ax2.set_ylim(0, max(vals_h) * 1.15 if vals_h else 10)
            ax2.set_ylabel("Percentual (%)")
            ax2.set_title("Condições de Habitação")
        else:
            ax2.set_title("Habitação\n(sem dados)", fontsize=10)
            ax2.text(
                0.5,
                0.5,
                "Não disponível",
                ha="center",
                va="center",
                fontsize=10,
                color=ODIN_MUTED,
            )
            ax2.set_ylim(0, 1)
            ax2.set_yticks([])

        fig.tight_layout()
        return _fig_to_bytes(fig)

    def _chart_docentes(self) -> bytes:
        _mpl_style()
        d = self.data
        etapas = list(d.docentes_superior_por_etapa.keys())
        if not etapas:
            etapas = list(d.adequacao_docente_por_etapa.keys())
        if not etapas:
            return b""
        doc_sup = [d.docentes_superior_por_etapa.get(e, 0) for e in etapas]
        afd = [d.adequacao_docente_por_etapa.get(e, 0) for e in etapas]
        alunos_turma = [d.alunos_por_turma_etapa.get(e, 0) for e in etapas]

        x = np.arange(len(etapas))
        w = 0.28
        fig, ax = plt.subplots(figsize=(10, 5.0))

        b1 = ax.bar(
            x - w,
            doc_sup,
            w,
            label="Docentes c/ Ensino Superior (%)",
            color=ODIN_BLUE,
            zorder=3,
        )
        b2 = ax.bar(
            x,
            afd,
            w,
            label="Adequação Funcional Docente (%)",
            color=ODIN_TEAL,
            zorder=3,
        )

        for bar, val in zip(b1, doc_sup, strict=False):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.3,
                f"{val:.1f}",
                ha="center",
                va="bottom",
                fontsize=7.5,
                fontweight="bold",
                color=ODIN_BLUE,
            )
        for bar, val in zip(b2, afd, strict=False):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.3,
                f"{val:.1f}",
                ha="center",
                va="bottom",
                fontsize=7.5,
                color=ODIN_TEAL,
            )

        ax2 = ax.twinx()
        ax2.plot(
            x + w / 2,
            alunos_turma,
            "o--",
            color=ODIN_ORANGE,
            linewidth=2,
            markersize=7,
            label="Alunos por Turma (eixo dir.)",
        )
        for i, (xi, val) in enumerate(zip(x, alunos_turma, strict=False)):
            ax2.text(
                xi + w / 2,
                val + 0.3,
                f"{val:.1f}",
                ha="center",
                va="bottom",
                fontsize=8,
                color=ODIN_ORANGE,
                fontweight="bold",
            )
        if alunos_turma:
            ax2.set_ylim(0, max(alunos_turma) * 1.2)
        else:
            ax2.set_ylim(0, 10)
        ax2.set_ylabel("Alunos/Turma", color=ODIN_ORANGE)

        ax.set_xticks(x)
        ax.set_xticklabels(etapas)
        ax.set_ylim(0, 115)
        ax.set_ylabel("Percentual (%)")
        ax.set_title("Qualificação Docente e Alunos por Turma")

        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="lower right")
        fig.tight_layout()
        return _fig_to_bytes(fig)

    def render(self) -> io.BytesIO:
        self._generate_charts()
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            topMargin=MARGIN_TOP + 0.4 * cm,
            bottomMargin=MARGIN_BOTTOM + 0.5 * cm,
            title=f"Dossiê do Município — {self.data.municipio_nome}",
            author="ODIN — LEMA/UFPB",
            subject=f"Relatório de indicadores de {self.data.municipio_nome}/{self.data.uf}",
        )
        doc._title = self._title

        self._build_cover()
        self._build_summary()
        self._build_educational()
        self._build_infrastructure()
        self._build_distribution()
        self._build_top_schools()
        self._build_socioeconomic()
        self._build_footer()

        doc.build(self._story, onFirstPage=_header_footer, onLaterPages=_header_footer)
        buf.seek(0)
        return buf

    def _build_cover(self) -> None:
        s = self.styles
        d = self.data
        self._story.extend(
            [
                Spacer(1, 6.5 * cm),
                Paragraph("Dossiê do Município", s["CoverTitle"]),
                Paragraph(f"{d.municipio_nome} / {d.uf}", s["CoverEntity"]),
                Spacer(1, 8),
                Paragraph(
                    f"Gerado em {_data_por_extenso(datetime.now())}", s["CoverDate"]
                ),
                Spacer(1, 2.5 * cm),
                Paragraph(
                    "Indicadores Educacionais e Socioeconômicos", s["CoverSubtitle"]
                ),
                Spacer(1, 0.6 * cm),
                Paragraph(
                    "Censo Escolar INEP/MEC · Censo Demográfico IBGE", s["CoverDate"]
                ),
                PageBreak(),
            ]
        )

    def _build_summary(self) -> None:
        s = self.styles
        d = self.data
        self._story.append(_section_header("Resumo Executivo", "📋"))
        self._story.append(Spacer(1, 10))

        pop_text = (
            f"{d.populacao_total:,}".replace(",", ".")
            if d.populacao_total
            else "dados não disponíveis"
        )
        self._story.append(
            Paragraph(
                f"Este dossiê apresenta um panorama completo dos indicadores educacionais e "
                f"socioeconômicos do município de <b>{d.municipio_nome}</b>, no estado da <b>{d.uf}</b>. "
                f"Com uma população estimada em <b>{pop_text} habitantes</b> (IBGE), "
                f"os dados educacionais são provenientes do Censo Escolar (INEP/MEC) e os "
                f"indicadores socioeconômicos do Censo Demográfico do IBGE.",
                s["BodyText"],
            )
        )
        self._story.append(Spacer(1, 10))

        kpis = [
            _kpi_card("Total de Escolas", str(d.total_escolas), ODIN_BLUE),
            _kpi_card(
                "Total de Matrículas",
                f"{d.total_alunos:,}".replace(",", "."),
                ODIN_TEAL,
            ),
            _kpi_card("Bairros Atendidos", str(d.total_bairros), ODIN_GREEN),
            _kpi_card("População", pop_text, ODIN_PURPLE),
        ]
        self._story.append(_kpi_row(kpis))
        self._story.append(Spacer(1, 8))

        kpis2 = []
        if d.ideb_por_etapa:
            for etapa, val in d.ideb_por_etapa.items():
                meta = (
                    "6,0"
                    if "Iniciais" in etapa
                    else "5,5"
                    if "Finais" in etapa
                    else "5,2"
                )
                color = (
                    ODIN_GREEN
                    if val >= 6.0
                    else ODIN_ORANGE
                    if val >= 4.5
                    else ODIN_RED
                )
                kpis2.append(_kpi_card(f"IDEB {etapa}", f"{val:.2f}", color))
        if d.aprovacao_por_etapa and "Anos Iniciais" in d.aprovacao_por_etapa:
            apro = d.aprovacao_por_etapa["Anos Iniciais"]
            kpis2.append(_kpi_card("Taxa de Aprovação", f"{apro:.1f}%", ODIN_GREEN))
        if kpis2:
            self._story.append(_kpi_row(kpis2[:4]))
            self._story.append(Spacer(1, 8))

        analysis_parts = []
        if d.ideb_por_etapa and "Anos Iniciais" in d.ideb_por_etapa:
            analysis_parts.append(
                f"IDEB nos Anos Iniciais é {d.ideb_por_etapa['Anos Iniciais']:.2f}"
            )
        if d.aprovacao_por_etapa and "Anos Iniciais" in d.aprovacao_por_etapa:
            analysis_parts.append(
                f"aprovação de {d.aprovacao_por_etapa['Anos Iniciais']:.1f}% nos Anos Iniciais"
            )
        if d.aprovacao_por_etapa and "Ensino Médio" in d.aprovacao_por_etapa:
            analysis_parts.append(
                f"{d.aprovacao_por_etapa['Ensino Médio']:.1f}% no Ensino Médio"
            )
        if analysis_parts:
            analysis_text = (
                "📌 <b>Análise geral:</b> " + "; ".join(analysis_parts) + "."
            )
            self._story.append(_analysis_box(analysis_text))
            self._story.append(Spacer(1, 12))

        header_res = ["Indicador", "Anos Iniciais", "Anos Finais", "Ensino Médio"]
        rows_res = []
        etapas = ["Anos Iniciais", "Anos Finais", "Ensino Médio"]
        # IDEB
        row = [Paragraph("<b>IDEB</b>", s["BodyText"])]
        for e in etapas:
            val = d.ideb_por_etapa.get(e)
            row.append(Paragraph(_ideb_colored(val), s["BodyText"]))
        rows_res.append(row)
        # Aprovação
        row = [Paragraph("<b>Aprovação (%)</b>", s["BodyText"])]
        for e in etapas:
            val = d.aprovacao_por_etapa.get(e)
            row.append(
                Paragraph(
                    _pct_colored(val, 80, 60)
                    if val is not None
                    else "<font color='#6C757D'>—</font>",
                    s["BodyText"],
                )
            )
        rows_res.append(row)
        # Abandono
        row = [Paragraph("<b>Abandono (%)</b>", s["BodyText"])]
        for e in etapas:
            val = d.abandono_por_etapa.get(e)
            if val is not None:
                c = ODIN_GREEN if val < 1 else ODIN_ORANGE if val < 5 else ODIN_RED
                txt = f'<font color="{c}"><b>{val:.1f}%</b></font>'
            else:
                txt = "<font color='#6C757D'>—</font>"
            row.append(Paragraph(txt, s["BodyText"]))
        rows_res.append(row)
        # Distorção
        row = [Paragraph("<b>Distorção Idade-Série (%)</b>", s["BodyText"])]
        for e in etapas:
            val = d.distorcao_idade_serie_por_etapa.get(e)
            if val is not None:
                c = ODIN_GREEN if val < 10 else ODIN_ORANGE if val < 25 else ODIN_RED
                txt = f'<font color="{c}"><b>{val:.1f}%</b></font>'
            else:
                txt = "<font color='#6C757D'>—</font>"
            row.append(Paragraph(txt, s["BodyText"]))
        rows_res.append(row)
        # Alunos por turma
        row = [Paragraph("<b>Alunos por Turma</b>", s["BodyText"])]
        for e in etapas:
            val = d.alunos_por_turma_etapa.get(e)
            row.append(
                Paragraph(f"{val:.1f}" if val is not None else "—", s["BodyText"])
            )
        rows_res.append(row)
        # Docentes c/ superior
        row = [Paragraph("<b>Docentes c/ Superior (%)</b>", s["BodyText"])]
        for e in etapas:
            val = d.docentes_superior_por_etapa.get(e)
            row.append(
                Paragraph(
                    _pct_colored(val, 90, 70)
                    if val is not None
                    else "<font color='#6C757D'>—</font>",
                    s["BodyText"],
                )
            )
        rows_res.append(row)

        self._story.append(
            _standard_table(
                header_res, rows_res, [5.5 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm]
            )
        )
        self._story.append(PageBreak())

    def _build_educational(self) -> None:
        s = self.styles
        d = self.data

        self._story.append(
            _section_header("Indicadores Educacionais — Desempenho", "📊")
        )
        self._story.append(Spacer(1, 10))

        self._story.append(
            Paragraph(
                "Os indicadores de desempenho escolar refletem a qualidade da aprendizagem e as condições "
                "de permanência dos alunos. O <b>IDEB</b> (Índice de Desenvolvimento da Educação Básica) "
                "combina proficiência e fluxo escolar. A meta nacional para Anos Iniciais é 6,0.",
                s["BodyText"],
            )
        )
        self._story.append(Spacer(1, 8))
        if "ideb_grouped" in self._charts:
            self._story.append(_chart_image(self._charts["ideb_grouped"], 15.5, 5.5))
            self._story.append(
                Paragraph(
                    "IDEB e Taxa de Aprovação por etapa. Linha tracejada = meta nacional.",
                    s["CaptionText"],
                )
            )
        self._story.append(Spacer(1, 8))
        if d.abandono_por_etapa or d.distorcao_idade_serie_por_etapa:
            self._story.append(
                Paragraph(
                    "Abandono Escolar e Distorção Idade-Série", s["SubSectionTitle"]
                )
            )
            self._story.append(
                Paragraph(
                    "O abandono e a distorção idade-série são indicadores críticos para a permanência.",
                    s["BodyText"],
                )
            )
            self._story.append(Spacer(1, 8))
            if "abandono_distorcao" in self._charts:
                self._story.append(
                    _chart_image(self._charts["abandono_distorcao"], 15.5, 4.8)
                )
                self._story.append(
                    Paragraph(
                        "Abandono escolar e distorção idade-série por etapa.",
                        s["CaptionText"],
                    )
                )
        self._story.append(PageBreak())

        self._story.append(
            _section_header("Corpo Docente e Condições de Ensino", "👩‍🏫")
        )
        self._story.append(Spacer(1, 10))
        self._story.append(
            Paragraph(
                "A qualificação docente e o tamanho das turmas são determinantes para a qualidade do ensino.",
                s["BodyText"],
            )
        )
        self._story.append(Spacer(1, 8))
        if "docentes" in self._charts:
            self._story.append(_chart_image(self._charts["docentes"], 15.5, 5.2))
            self._story.append(
                Paragraph(
                    "Qualificação docente (%) e número médio de alunos por turma.",
                    s["CaptionText"],
                )
            )
        self._story.append(Spacer(1, 10))

        header_doc = [
            "Etapa",
            "Docentes c/ Superior",
            "Adequação Docente (AFD)",
            "Horas-Aula/Dia",
            "Alunos/Turma",
        ]
        rows_doc = []
        etapas = ["Anos Iniciais", "Anos Finais", "Ensino Médio"]
        for e in etapas:
            sup = d.docentes_superior_por_etapa.get(e)
            afd = d.adequacao_docente_por_etapa.get(e)
            horas = d.horas_aula_por_etapa.get(e)
            alunos = d.alunos_por_turma_etapa.get(e)
            rows_doc.append(
                [
                    Paragraph(f"<b>{e}</b>", s["BodyText"]),
                    Paragraph(
                        _pct_colored(sup, 90, 70)
                        if sup is not None
                        else "<font color='#6C757D'>—</font>",
                        s["BodyText"],
                    ),
                    Paragraph(
                        _pct_colored(afd, 85, 70)
                        if afd is not None
                        else "<font color='#6C757D'>—</font>",
                        s["BodyText"],
                    ),
                    Paragraph(
                        f"{horas:.1f}h" if horas is not None else "—", s["BodyText"]
                    ),
                    Paragraph(
                        f"{alunos:.1f}" if alunos is not None else "—", s["BodyText"]
                    ),
                ]
            )
        self._story.append(
            _standard_table(
                header_doc, rows_doc, [4.5 * cm, 3.5 * cm, 3.8 * cm, 2.7 * cm, 2.5 * cm]
            )
        )
        self._story.append(Spacer(1, 10))

        # Removed matrículas section because data may be unreliable

    def _build_infrastructure(self) -> None:
        s = self.styles
        d = self.data
        if not d.infraestrutura:
            return
        self._story.append(_section_header("Infraestrutura Escolar", "🏫"))
        self._story.append(Spacer(1, 10))
        self._story.append(
            Paragraph(
                f"A infraestrutura das {d.total_escolas} escolas ativas. Itens básicos têm cobertura universal; "
                "recursos pedagógicos apresentam déficit.",
                s["BodyText"],
            )
        )
        self._story.append(Spacer(1, 8))
        if "infra_bars" in self._charts:
            self._story.append(_chart_image(self._charts["infra_bars"], 15.5, 7.5))
            self._story.append(
                Paragraph(
                    "Cobertura de infraestrutura. Verde ≥ 70% (adequado), laranja 40–69% (atenção), vermelho < 40% (crítico).",
                    s["CaptionText"],
                )
            )
        self._story.append(Spacer(1, 10))

        header_inf = [
            "Item de Infraestrutura",
            "Cobertura",
            "Status",
            "Nº Estimado de Escolas",
        ]
        rows_inf = []
        infra_sorted = sorted(
            d.infraestrutura.items(), key=lambda x: x[1], reverse=True
        )
        for label, val in infra_sorted:
            status = (
                "✔ Adequado"
                if val >= 70
                else ("⚠ Atenção" if val >= 40 else "✗ Crítico")
            )
            status_color = (
                ODIN_GREEN if val >= 70 else (ODIN_ORANGE if val >= 40 else ODIN_RED)
            )
            n_escolas = int(d.total_escolas * val / 100) if d.total_escolas else 0
            rows_inf.append(
                [
                    Paragraph(f"<b>{label}</b>", s["BodyText"]),
                    Paragraph(
                        f'<font color="{status_color}"><b>{val:.1f}%</b></font>',
                        s["BodyText"],
                    ),
                    Paragraph(
                        f'<font color="{status_color}"><b>{status}</b></font>',
                        s["BodyText"],
                    ),
                    Paragraph(f"≈ {n_escolas} de {d.total_escolas}", s["BodyText"]),
                ]
            )
        self._story.append(
            _standard_table(
                header_inf, rows_inf, [6.0 * cm, 2.8 * cm, 3.0 * cm, 4.2 * cm]
            )
        )
        self._story.append(PageBreak())

    def _build_distribution(self) -> None:
        s = self.styles
        d = self.data
        if not d.escolas_por_dependencia and not d.escolas_por_zona:
            return
        self._story.append(_section_header("Distribuição das Escolas", "🗺"))
        self._story.append(Spacer(1, 10))
        if "dependencia_zona" in self._charts:
            self._story.append(
                _chart_image(self._charts["dependencia_zona"], 15.5, 5.2)
            )
            self._story.append(
                Paragraph(
                    "Distribuição por dependência administrativa e localização.",
                    s["CaptionText"],
                )
            )
        self._story.append(Spacer(1, 10))
        if d.escolas_por_dependencia:
            header_dep = [
                "Rede",
                "Nº de Escolas",
                "Participação (%)",
                "Matrículas Estimadas",
            ]
            total_dep = sum(d.escolas_por_dependencia.values())
            rows_dep = []
            for rede, qtd in d.escolas_por_dependencia.items():
                pct = (qtd / total_dep * 100) if total_dep else 0
                rows_dep.append(
                    [
                        Paragraph(f"<b>{rede}</b>", s["BodyText"]),
                        Paragraph(
                            f'<font color="{ODIN_BLUE}"><b>{qtd}</b></font>',
                            s["BodyText"],
                        ),
                        Paragraph(f"{pct:.1f}%", s["BodyText"]),
                        Paragraph(
                            f"≈ {int(qtd * (d.total_alunos / total_dep if total_dep else 0)):,}".replace(
                                ",", "."
                            ),
                            s["BodyText"],
                        ),
                    ]
                )
            # Removed total row because it may not match the actual total_escolas
            self._story.append(
                _standard_table(
                    header_dep, rows_dep, [4.5 * cm, 3.5 * cm, 3.5 * cm, 5.0 * cm]
                )
            )
        self._story.append(PageBreak())

    def _build_top_schools(self) -> None:
        s = self.styles
        d = self.data
        if not d.top_escolas:
            return
        self._story.append(
            _section_header("Top Escolas por IDEB — Anos Iniciais", "🏆")
        )
        self._story.append(Spacer(1, 10))
        self._story.append(
            Paragraph(
                "Ranking das escolas com maiores IDEB nos Anos Iniciais. "
                "As cores destacam desempenho excelente (≥ 6,5), muito bom (6,0–6,4) e bom (< 6,0).",
                s["BodyText"],
            )
        )
        self._story.append(Spacer(1, 8))
        if "top_schools" in self._charts:
            self._story.append(_chart_image(self._charts["top_schools"], 15.5, 5.8))
            self._story.append(
                Paragraph(
                    "Ranking das 10 escolas com maior IDEB (Anos Iniciais).",
                    s["CaptionText"],
                )
            )
        self._story.append(Spacer(1, 10))

        header_esc = ["Posição", "Nome da Escola", "IDEB", "Rede", "Localização"]
        rows_esc = []
        for i, school in enumerate(d.top_escolas[:10], 1):
            medal = (
                "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"{i}°"))
            )
            ideb_v = school.get("ideb", 0)
            ideb_color = ODIN_GOLD if ideb_v >= 6.5 else ODIN_GREEN
            rows_esc.append(
                [
                    Paragraph(f"<b>{medal}</b>", s["BodyText"]),
                    Paragraph(f"<b>{school.get('nome', '')}</b>", s["BodyText"]),
                    Paragraph(
                        f'<font color="{ideb_color}"><b>{ideb_v:.1f}</b></font>',
                        s["BodyText"],
                    ),
                    Paragraph(school.get("dependencia", "-"), s["BodyText"]),
                    Paragraph(school.get("localizacao", "-"), s["BodyText"]),
                ]
            )
        self._story.append(
            _standard_table(
                header_esc, rows_esc, [2.0 * cm, 6.5 * cm, 2.0 * cm, 2.8 * cm, 2.7 * cm]
            )
        )
        self._story.append(PageBreak())

    def _build_socioeconomic(self) -> None:
        s = self.styles
        d = self.data
        has_demo = (
            d.estrutura_etaria or d.raca or d.genero or d.populacao_total is not None
        )
        has_san = d.saneamento or d.habitacao
        if not has_demo and not has_san:
            return

        self._story.append(_section_header("Contexto Socioeconômico", "👥"))
        self._story.append(Spacer(1, 10))

        if has_demo:
            self._story.append(Paragraph("Perfil Demográfico", s["SubSectionTitle"]))
            if d.populacao_total:
                self._story.append(
                    Paragraph(
                        f"População total: <b>{d.populacao_total:,}".replace(",", ".")
                        + " habitantes</b> (IBGE).",
                        s["BodyText"],
                    )
                )
            if d.taxa_analfabetismo is not None:
                self._story.append(
                    Paragraph(
                        f"Taxa de analfabetismo (15+ anos): <b>{d.taxa_analfabetismo:.1f}%</b>.",
                        s["BodyText"],
                    )
                )
            self._story.append(Spacer(1, 6))

            kpis_demo = []
            if d.taxa_analfabetismo is not None:
                kpis_demo.append(
                    _kpi_card(
                        "Analfabetismo (15+)", f"{d.taxa_analfabetismo:.1f}%", ODIN_RED
                    )
                )
            if d.razao_dependencia is not None:
                kpis_demo.append(
                    _kpi_card(
                        "Razão de Dependência",
                        f"{d.razao_dependencia:.1f}",
                        ODIN_ORANGE,
                    )
                )
            if d.pct_responsavel_feminino is not None:
                kpis_demo.append(
                    _kpi_card(
                        "Responsável feminino",
                        f"{d.pct_responsavel_feminino:.1f}%",
                        ODIN_PURPLE,
                    )
                )
            if d.media_moradores_domicilio is not None:
                kpis_demo.append(
                    _kpi_card(
                        "Moradores/Domicílio",
                        f"{d.media_moradores_domicilio:.2f}",
                        ODIN_TEAL,
                    )
                )
            if kpis_demo:
                self._story.append(_kpi_row(kpis_demo))
                self._story.append(Spacer(1, 8))

            if "estrutura_etaria" in self._charts and (d.estrutura_etaria or d.raca):
                self._story.append(
                    _chart_image(self._charts["estrutura_etaria"], 15.5, 5.2)
                )
                self._story.append(
                    Paragraph("Estrutura etária e composição racial.", s["CaptionText"])
                )
                self._story.append(Spacer(1, 8))

            header_demo = ["Indicador Demográfico", "Valor", "Referência"]
            rows_demo = []
            if d.populacao_total is not None:
                rows_demo.append(
                    [
                        Paragraph("População total", s["BodyText"]),
                        Paragraph(
                            f"{d.populacao_total:,}".replace(",", "."), s["BodyText"]
                        ),
                        Paragraph("IBGE", s["BodyText"]),
                    ]
                )
            if d.taxa_analfabetismo is not None:
                rows_demo.append(
                    [
                        Paragraph("Taxa de analfabetismo (15+)", s["BodyText"]),
                        Paragraph(f"{d.taxa_analfabetismo:.1f}%", s["BodyText"]),
                        Paragraph("IBGE", s["BodyText"]),
                    ]
                )
            if d.razao_dependencia is not None:
                rows_demo.append(
                    [
                        Paragraph("Razão de dependência", s["BodyText"]),
                        Paragraph(f"{d.razao_dependencia:.1f}", s["BodyText"]),
                        Paragraph("IBGE", s["BodyText"]),
                    ]
                )
            if d.pct_responsavel_feminino is not None:
                rows_demo.append(
                    [
                        Paragraph("Responsável feminino", s["BodyText"]),
                        Paragraph(f"{d.pct_responsavel_feminino:.1f}%", s["BodyText"]),
                        Paragraph("IBGE", s["BodyText"]),
                    ]
                )
            if d.media_moradores_domicilio is not None:
                rows_demo.append(
                    [
                        Paragraph("Média moradores/domicílio", s["BodyText"]),
                        Paragraph(f"{d.media_moradores_domicilio:.2f}", s["BodyText"]),
                        Paragraph("IBGE", s["BodyText"]),
                    ]
                )
            if d.estrutura_etaria:
                for key, val in d.estrutura_etaria.items():
                    rows_demo.append(
                        [
                            Paragraph(key, s["BodyText"]),
                            Paragraph(f"{val:.1f}%", s["BodyText"]),
                            Paragraph("IBGE", s["BodyText"]),
                        ]
                    )
            if d.raca:
                for key, val in d.raca.items():
                    rows_demo.append(
                        [
                            Paragraph(f"Pop. {key.lower()}", s["BodyText"]),
                            Paragraph(f"{val:.1f}%", s["BodyText"]),
                            Paragraph("IBGE", s["BodyText"]),
                        ]
                    )
            if d.genero:
                for key, val in d.genero.items():
                    rows_demo.append(
                        [
                            Paragraph(f"Pop. {key.lower()}", s["BodyText"]),
                            Paragraph(f"{val:.1f}%", s["BodyText"]),
                            Paragraph("IBGE", s["BodyText"]),
                        ]
                    )
            if rows_demo:
                self._story.append(
                    _standard_table(
                        header_demo, rows_demo, [7.5 * cm, 4.5 * cm, 4.0 * cm]
                    )
                )
                self._story.append(Spacer(1, 10))

        if has_san:
            self._story.append(
                Paragraph("Saneamento e Habitação", s["SubSectionTitle"])
            )
            self._story.append(
                Paragraph(
                    "Condições de saneamento e habitação impactam saúde e frequência escolar.",
                    s["BodyText"],
                )
            )
            self._story.append(Spacer(1, 6))
            if "saneamento_habitacao" in self._charts:
                self._story.append(
                    _chart_image(self._charts["saneamento_habitacao"], 15.5, 5.5)
                )
                self._story.append(
                    Paragraph(
                        "Saneamento básico e condições de habitação.", s["CaptionText"]
                    )
                )
                self._story.append(Spacer(1, 8))

            header_san = ["Indicador", "Valor (%)", "Classificação"]
            rows_san = []
            if d.saneamento:
                for key, val in d.saneamento.items():
                    c = ODIN_GREEN if val >= 70 else ODIN_ORANGE
                    rows_san.append(
                        [
                            Paragraph(key, s["BodyText"]),
                            Paragraph(
                                f'<font color="{c}"><b>{val:.1f}%</b></font>',
                                s["BodyText"],
                            ),
                            Paragraph(
                                "Adequado" if val >= 70 else "Atenção", s["BodyText"]
                            ),
                        ]
                    )
            if d.habitacao:
                for key, val in d.habitacao.items():
                    rows_san.append(
                        [
                            Paragraph(key, s["BodyText"]),
                            Paragraph(f"{val:.1f}%", s["BodyText"]),
                            Paragraph("—", s["BodyText"]),
                        ]
                    )
            if rows_san:
                self._story.append(
                    _standard_table(
                        header_san, rows_san, [6.5 * cm, 3.5 * cm, 6.0 * cm]
                    )
                )
        self._story.append(PageBreak())

    def _build_footer(self) -> None:
        s = self.styles
        self._story.append(Spacer(1, 20))
        self._story.append(
            HRFlowable(
                width="100%", thickness=0.5, color=colors.HexColor(ODIN_MEDIUM_GRAY)
            )
        )
        self._story.append(Spacer(1, 8))
        self._story.append(Paragraph("Metodologia e Fontes", s["SubSectionTitle"]))
        self._story.append(
            Paragraph(
                "Este dossiê foi gerado pelo <b>ODIN — Observatório de Dados Integrados do Nordeste</b>, "
                "iniciativa do <b>LEMA/UFPB</b>. Os <b>dados educacionais</b> são do Censo Escolar INEP/MEC "
                "e os <b>dados socioeconômicos</b> do Censo Demográfico IBGE. "
                "Para mais informações, acesse o portal do ODIN.",
                s["BodyText"],
            )
        )
        self._story.append(Spacer(1, 5))
        self._story.append(
            Paragraph(
                f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}  ·  "
                f"Município: {self.data.municipio_nome}/{self.data.uf}  ·  "
                f"Código IBGE: {self.data.municipio_id}",
                s["SmallMuted"],
            )
        )


class StateDossierPDF:
    def __init__(self, data: StateDossierData) -> None:
        self.data = data
        self.styles = _build_styles()
        self._story: list[Any] = []
        self._charts: dict[str, bytes] = {}
        self._title = f"{data.estado_nome} / {data.uf}"

    def add_chart(self, key: str, chart_bytes: bytes) -> None:
        self._charts[key] = chart_bytes

    def render(self) -> io.BytesIO:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            topMargin=MARGIN_TOP + 0.4 * cm,
            bottomMargin=MARGIN_BOTTOM + 0.5 * cm,
            title=f"Dossiê do Estado — {self.data.estado_nome}",
            author="ODIN — LEMA/UFPB",
            subject=f"Relatório de indicadores do estado {self.data.estado_nome}",
        )
        doc._title = self._title

        s = self.styles
        d = self.data
        self._story.extend(
            [
                Spacer(1, 6.5 * cm),
                Paragraph("Dossiê do Estado", s["CoverTitle"]),
                Paragraph(f"{d.estado_nome} / {d.uf}", s["CoverEntity"]),
                Spacer(1, 8),
                Paragraph(
                    f"Gerado em {_data_por_extenso(datetime.now())}", s["CoverDate"]
                ),
                Spacer(1, 2.5 * cm),
                Paragraph("Indicadores Educacionais Consolidados", s["CoverSubtitle"]),
                Spacer(1, 0.6 * cm),
                Paragraph(
                    "Censo Escolar INEP/MEC · Censo Demográfico IBGE", s["CoverDate"]
                ),
                PageBreak(),
                _section_header("Resumo Executivo", "📋"),
                Spacer(1, 10),
                Paragraph(
                    f"Este dossiê apresenta um panorama consolidado dos indicadores educacionais "
                    f"do estado de <b>{d.estado_nome}</b>, agregando dados de todos os "
                    f"{d.total_municipios} municípios.",
                    s["BodyText"],
                ),
                Spacer(1, 10),
                _kpi_row(
                    [
                        _kpi_card("Municípios", str(d.total_municipios), ODIN_BLUE),
                        _kpi_card("Total de Escolas", str(d.total_escolas), ODIN_TEAL),
                        _kpi_card(
                            "Total de Alunos",
                            f"{d.total_alunos:,}".replace(",", "."),
                            ODIN_GREEN,
                        ),
                    ]
                ),
                Spacer(1, 10),
            ]
        )
        if d.ideb_por_etapa:
            header = ["Etapa", "IDEB"]
            rows = [[e, f"{v:.2f}"] for e, v in d.ideb_por_etapa.items()]
            self._story.append(
                _standard_table(header, rows, [CONTENT_W / 2, CONTENT_W / 2])
            )
        self._story.append(PageBreak())
        self._story.append(Paragraph("Metodologia e Fontes", s["SubSectionTitle"]))
        self._story.append(
            Paragraph(
                "Este relatório foi gerado pelo ODIN — Observatório de Dados Integrados do Nordeste.",
                s["BodyText"],
            )
        )
        self._story.append(Spacer(1, 5))
        self._story.append(
            Paragraph(
                f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
                s["SmallMuted"],
            )
        )

        doc.build(self._story, onFirstPage=_header_footer, onLaterPages=_header_footer)
        buf.seek(0)
        return buf
