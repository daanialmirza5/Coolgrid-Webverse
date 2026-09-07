"""PDF report generation (ReportLab). Gathers the current heat situation,
drivers, prediction, and the latest simulation/optimization for a ward (or
a city-wide summary when no ward is given) into a structured `sections_json`
record, then renders it to a downloadable PDF."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..models.city import City, Ward
from ..models.intervention import OptimizationRun, Simulation
from ..models.report import Report, ReportStatus
from ..models.user import User
from ..schemas.report import ReportRequest
from . import heat_service, prediction_service
from .ml_registry import get_ml_registry

settings = get_settings()


def _gather_sections(db: Session, city: City, ward: Ward | None, simulation: Simulation | None, opt_run: OptimizationRun | None) -> dict:
    dashboard = heat_service.dashboard_summary(db, city)
    registry = get_ml_registry()

    sections: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "city": {"name": city.name, "is_demo": city.is_demo},
        "executive_summary": (
            f"CoolGrid's DETECT-EXPLAIN-PREDICT-SIMULATE-OPTIMIZE pipeline analyzed "
            f"{dashboard.city_name}. City-wide average land surface temperature is "
            f"{dashboard.avg_lst}°C (max {dashboard.max_lst}°C) with "
            f"{dashboard.hotspot_count} high/critical-risk wards exposing an estimated "
            f"{dashboard.population_exposed:,} residents to elevated heat risk."
        ),
        "heat_situation": dashboard.model_dump(mode="json"),
        "data_sources": registry.providers.status(),
        "methodology": (
            "Heat detection uses an XGBoost regressor trained on CoolGrid's demo "
            "dataset (NDVI, NDBI, albedo, built-up density, vegetation/water cover, "
            "road density, population density, humidity, wind, solar radiation) to "
            "predict land surface temperature, with SHAP for driver attribution. "
            "Predictions blend the detector with a simplified surface energy-balance "
            "physics model (Oke, 1982-style Rn=H+LE+G decomposition). Interventions "
            "are simulated by perturbing physical surface attributes and re-solving "
            "the energy balance; the optimizer performs a constraint-filtered grid "
            "search over intervention coverage levels, ranked by a weighted "
            "multi-objective score. All figures are DEMO-DATA-DERIVED estimates, not "
            "validated real-world measurements."
        ),
    }

    if ward is not None:
        hotspot = heat_service.get_hotspot_for_ward(db, ward, city)
        drivers = heat_service.driver_analysis(db, ward)
        prediction = prediction_service.predict_for_ward(db, ward)
        sections["ward"] = {"id": str(ward.id), "name": ward.name, "archetype": ward.archetype.value}
        sections["hotspot"] = hotspot.model_dump(mode="json") if hotspot else None
        sections["drivers"] = drivers.model_dump(mode="json")
        sections["prediction"] = prediction.model_dump(mode="json")

    if simulation is not None:
        sections["simulation"] = {
            "interventions": simulation.interventions_json,
            "baseline_lst": simulation.baseline_lst,
            "simulated_lst": simulation.simulated_lst,
            "expected_cooling_c": simulation.expected_cooling_c,
            "cost_usd": simulation.cost_usd,
            "population_benefited": simulation.population_benefited,
            "risk_reduction_pct": simulation.risk_reduction_pct,
            "confidence": simulation.confidence,
        }

    if opt_run is not None:
        sections["optimization"] = {
            "constraints": opt_run.constraints_json,
            "strategies": opt_run.results_json,
        }
        if opt_run.results_json:
            top = opt_run.results_json[0]
            sections["recommended_actions"] = top["reason"]
            sections["expected_impact"] = {
                "cooling_c": top["expected_cooling_c"],
                "population_benefited": top["population_benefited"],
                "risk_reduction_pct": top["risk_reduction_pct"],
                "confidence": top["confidence"],
            }

    return sections


def _render_pdf(report: Report, sections: dict) -> str:
    settings.generated_reports_dir.mkdir(parents=True, exist_ok=True)
    file_path = settings.generated_reports_dir / f"{report.id}.pdf"

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=colors.HexColor("#0f172a"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.HexColor("#0369a1"), spaceBefore=12)
    body = styles["BodyText"]
    demo_note = ParagraphStyle("Demo", parent=styles["Italic"], textColor=colors.HexColor("#b45309"))
    cell_style = ParagraphStyle("Cell", parent=styles["BodyText"], fontSize=9, leading=11)

    def cell(text: str) -> Paragraph:
        return Paragraph(str(text), cell_style)

    doc = SimpleDocTemplate(str(file_path), pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    story = [
        Paragraph(report.title, h1),
        Paragraph(f"Generated {sections['generated_at']} · CoolGrid Urban Heat Intelligence Platform", body),
        Paragraph("DEMO DATA: figures in this report are derived from CoolGrid's synthetic demonstration dataset, not real satellite/weather observations.", demo_note),
        Spacer(1, 12),
        Paragraph("Executive Summary", h2),
        Paragraph(sections["executive_summary"], body),
        Paragraph("Heat Situation", h2),
    ]

    hs = sections["heat_situation"]
    story.append(
        Table(
            [
                ["Metric", "Value"],
                ["Average LST", f"{hs['avg_lst']} °C"],
                ["Max LST", f"{hs['max_lst']} °C"],
                ["High/Critical wards", str(hs["hotspot_count"])],
                ["Population exposed", f"{hs['population_exposed']:,}"],
                ["Avg vegetation cover", f"{hs['avg_vegetation_pct']}%"],
                ["Avg built-up density", f"{hs['avg_built_up_pct']}%"],
            ],
            colWidths=[7 * cm, 7 * cm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0369a1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]),
        )
    )

    if "ward" in sections:
        story.append(Paragraph(f"Ward Focus: {sections['ward']['name']}", h2))
        if sections.get("hotspot"):
            hot = sections["hotspot"]
            story.append(Paragraph(
                f"LST {hot['lst_celsius']}°C (range {hot['lst_lower']}-{hot['lst_upper']}°C), "
                f"heat score {hot['heat_score']}/100, risk level {hot['risk_level']}, "
                f"confidence {hot['confidence']*100:.0f}%.", body))

        story.append(Paragraph("Heat Drivers", h2))
        story.append(Paragraph(sections["drivers"]["narrative"], body))
        driver_rows = [["Driver", "Direction", "Contribution %"]]
        for d in sections["drivers"]["drivers"][:6]:
            driver_rows.append([cell(d["label"]), "Warms" if d["direction"] == "increases_heat" else "Cools", f"{d['relative_contribution_pct']}%"])
        story.append(Table(driver_rows, colWidths=[7 * cm, 3.5 * cm, 3.5 * cm], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0369a1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ])))

        story.append(Paragraph("Prediction", h2))
        pred = sections["prediction"]
        pred_rows = [["Horizon", "Predicted LST", "Change", "Confidence"]]
        for p in pred["points"]:
            pred_rows.append([f"{p['horizon_days']}d", f"{p['predicted_lst']}°C", f"{p['change_from_current_c']:+.1f}°C", f"{p['confidence']*100:.0f}%"])
        story.append(Table(pred_rows, colWidths=[3.5 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0369a1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ])))
        story.append(Paragraph(pred["points"][0]["disclaimer"], demo_note))

    if "simulation" in sections:
        story.append(Paragraph("Intervention Scenario", h2))
        sim = sections["simulation"]
        story.append(Paragraph(
            f"Baseline {sim['baseline_lst']}°C → Simulated {sim['simulated_lst']}°C "
            f"(cooling {sim['expected_cooling_c']}°C), cost ${sim['cost_usd']:,.0f}, "
            f"benefiting ~{sim['population_benefited']:,} residents.", body))

    if "optimization" in sections:
        story.append(Paragraph("Optimization", h2))
        opt_rows = [["Rank", "Interventions", "Cooling", "Cost", "Confidence"]]
        for s in sections["optimization"]["strategies"][:5]:
            names = ", ".join(i["label"] for i in s["interventions"])
            opt_rows.append([str(s["rank"]), cell(names), f"{s['expected_cooling_c']}°C", f"${s['cost_usd']:,.0f}", f"{s['confidence']*100:.0f}%"])
        story.append(Table(opt_rows, colWidths=[1.5 * cm, 6.5 * cm, 2.5 * cm, 3 * cm, 2.5 * cm], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0369a1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ])))

        story.append(Paragraph("Recommended Actions", h2))
        story.append(Paragraph(sections.get("recommended_actions", "N/A"), body))

        story.append(Paragraph("Expected Impact & Confidence", h2))
        impact = sections.get("expected_impact", {})
        story.append(Paragraph(
            f"Cooling: {impact.get('cooling_c')}°C · Population benefited: {impact.get('population_benefited', 0):,} · "
            f"Risk reduction: {impact.get('risk_reduction_pct')}% · Confidence: {impact.get('confidence', 0)*100:.0f}%", body))

    story.append(Paragraph("Data Sources", h2))
    ds = sections["data_sources"]
    story.append(Paragraph(
        f"Satellite: {ds['satellite']['provider']} (demo={ds['satellite']['is_demo']}) · "
        f"Weather: {ds['weather']['provider']} (demo={ds['weather']['is_demo']}) · "
        f"Urban: {ds['urban']['provider']} (demo={ds['urban']['is_demo']}) · "
        f"Population: {ds['population']['provider']} (demo={ds['population']['is_demo']})", body))

    story.append(Paragraph("Methodology", h2))
    story.append(Paragraph(sections["methodology"], body))

    doc.build(story)
    return str(file_path)


def create_report(db: Session, request: ReportRequest, user: User | None) -> Report:
    city = db.get(City, request.city_id) if request.city_id else heat_service.get_demo_city(db)
    ward = db.get(Ward, request.ward_id) if request.ward_id else None
    simulation = db.get(Simulation, request.simulation_id) if request.simulation_id else None
    opt_run = db.get(OptimizationRun, request.optimization_run_id) if request.optimization_run_id else None

    title = request.title or (f"CoolGrid Report – {ward.name}" if ward else f"CoolGrid City Report – {city.name}")

    report = Report(
        city_id=city.id, ward_id=ward.id if ward else None, user_id=user.id if user else None,
        title=title, status=ReportStatus.GENERATING, sections_json={},
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    try:
        sections = _gather_sections(db, city, ward, simulation, opt_run)
        file_path = _render_pdf(report, sections)
        report.sections_json = sections
        report.file_path = file_path
        report.status = ReportStatus.READY
    except Exception as e:  # noqa: BLE001 -- report generation failures must surface to the UI, not crash the request
        report.status = ReportStatus.FAILED
        report.error_message = str(e)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: uuid.UUID) -> Report | None:
    return db.get(Report, report_id)


def list_reports(db: Session, user: User) -> list[Report]:
    return db.execute(
        select(Report).where(Report.user_id == user.id).order_by(Report.created_at.desc())
    ).scalars().all()
