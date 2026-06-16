from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from backend.core.config import get_settings
from backend.models.schemas import ResearchReport, SourceSummary
from backend.services.llm_client import LLMClient
from backend.services.web_collector import WebCollector


class ResearchAgent:
    """Coordinates source collection, summarization, synthesis, and report persistence."""

    def __init__(self) -> None:
        self.cfg = get_settings()
        self.collector = WebCollector()
        self.llm = LLMClient()

    def _summarize_source(self, company: str, item: dict[str, Any]) -> SourceSummary:
        """Summarize one collected source into a compact evidence object."""
        title = item.get("title") or "Untitled source"
        url = item.get("url") or ""
        text = item.get("text") or ""

        if not text.strip():
            return SourceSummary(
                title=title,
                url=url,
                extracted_chars=0,
                summary=f"Source unavailable: {item.get('error', 'No extracted text')}",
            )

        prompt = f"""
Company: {company}
Source title: {title}
URL: {url}

Source excerpt:
{text[:6000]}

Summarize information relevant to business model, products, market position, competitors, risks, and strategic signals in 5 concise bullets.
Use cautious wording and do not invent facts beyond the source excerpt.
""".strip()

        return SourceSummary(
            title=title,
            url=url,
            extracted_chars=len(text),
            summary=self.llm.generate(prompt),
        )

    def run(
        self,
        company: str,
        industry_hint: str | None,
        focus_area: str | None,
        sources: list[str],
    ) -> ResearchReport:
        """Run the complete competitive intelligence workflow."""
        collected_items = self.collector.collect(company, sources)
        summaries = [self._summarize_source(company, item) for item in collected_items]

        evidence = "\n\n".join(
            [
                f"SOURCE: {s.title}\nURL: {s.url}\nSUMMARY:\n{s.summary}"
                for s in summaries
            ]
        )

        prompt = f"""
Create a competitive intelligence report for: {company}
Industry hint: {industry_hint or 'not provided'}
Research focus: {focus_area or 'general market and competitor analysis'}

Evidence collected:
{evidence}

Return a valid JSON object with these exact keys:
- executive_summary
- company_overview
- competitors
- swot
- market_signals
- strategic_recommendations

Requirements:
- competitors must be a list of objects with: name, rationale, relative_position, likely_strength.
- swot must contain four arrays: strengths, weaknesses, opportunities, threats.
- market_signals must be an array of concise strings.
- strategic_recommendations must be an array of concise strings.
- Use cautious wording when evidence is incomplete.
- Do not include markdown outside the JSON object.
""".strip()

        data = self.llm.generate_json(prompt)

        if "raw_response" in data:
            data = {
                "executive_summary": data["raw_response"],
                "company_overview": "The local model returned non-JSON output. Review the generated summary for useful findings.",
                "competitors": [],
                "swot": {
                    "strengths": [],
                    "weaknesses": [],
                    "opportunities": [],
                    "threats": [],
                },
                "market_signals": [],
                "strategic_recommendations": [],
            }

        markdown = self._to_markdown(company, data, summaries)

        report = ResearchReport(
            company_name=company,
            industry_hint=industry_hint,
            focus_area=focus_area,
            executive_summary=data.get("executive_summary", ""),
            company_overview=data.get("company_overview", ""),
            competitors=data.get("competitors", []),
            swot=data.get(
                "swot",
                {
                    "strengths": [],
                    "weaknesses": [],
                    "opportunities": [],
                    "threats": [],
                },
            ),
            market_signals=data.get("market_signals", []),
            strategic_recommendations=data.get("strategic_recommendations", []),
            sources=summaries,
            markdown_report=markdown,
        )

        self._save_report(report)
        return report

    def _to_markdown(
        self,
        company: str,
        data: dict[str, Any],
        sources: list[SourceSummary],
    ) -> str:
        """Convert structured report data into a Markdown report."""
        lines: list[str] = [
            f"# AutoResearch AI Report: {company}",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## Executive Summary",
            str(data.get("executive_summary", "")),
            "",
            "## Company Overview",
            str(data.get("company_overview", "")),
            "",
            "## Competitor Landscape",
        ]

        competitors = data.get("competitors", [])
        if competitors:
            for competitor in competitors:
                if isinstance(competitor, dict):
                    lines.append(
                        f"- **{competitor.get('name', 'Unknown')}** — "
                        f"{competitor.get('rationale', '')} "
                        f"Relative position: {competitor.get('relative_position', '')}. "
                        f"Strength: {competitor.get('likely_strength', '')}"
                    )
                else:
                    lines.append(f"- {competitor}")
        else:
            lines.append("- No competitors were confidently identified from the collected evidence.")

        lines.extend(["", "## SWOT Analysis"])
        swot = data.get("swot", {}) if isinstance(data.get("swot", {}), dict) else {}
        for key in ["strengths", "weaknesses", "opportunities", "threats"]:
            lines.append(f"### {key.title()}")
            values = swot.get(key, [])
            if values:
                for value in values:
                    lines.append(f"- {value}")
            else:
                lines.append("- Not enough evidence available.")
            lines.append("")

        lines.append("## Market Signals")
        market_signals = data.get("market_signals", [])
        if market_signals:
            for signal in market_signals:
                lines.append(f"- {signal}")
        else:
            lines.append("- No clear market signals were extracted.")

        lines.extend(["", "## Strategic Recommendations"])
        recommendations = data.get("strategic_recommendations", [])
        if recommendations:
            for recommendation in recommendations:
                lines.append(f"- {recommendation}")
        else:
            lines.append("- No strategic recommendations were generated from the available evidence.")

        lines.extend(["", "## Sources"])
        if sources:
            for source in sources:
                lines.append(
                    f"- [{source.title}]({source.url}) — {source.extracted_chars} characters extracted"
                )
        else:
            lines.append("- No sources were collected.")

        return "\n".join(lines)

    def _save_report(self, report: ResearchReport) -> None:
        """Persist report as JSON and Markdown files."""
        rid = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        self.cfg.report_path.mkdir(parents=True, exist_ok=True)
        (self.cfg.report_path / f"{rid}.json").write_text(
            report.model_dump_json(indent=2),
            encoding="utf-8",
        )
        (self.cfg.report_path / f"{rid}.md").write_text(
            report.markdown_report,
            encoding="utf-8",
        )
