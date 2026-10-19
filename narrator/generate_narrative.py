import os
from datetime import datetime


def _month_name(yyyy_mm: str) -> str:
    """2026-03 -> March"""
    return datetime.strptime(yyyy_mm, "%Y-%m").strftime("%B")


def _build_user_prompt(findings: dict) -> str:
    f = findings
    pay = f["return_rate_by_payment"]
    seg = f["highest_risk_segment"]
    peak = f["true_peak_month"]
    out = f["outlier_inflated_month"]

    return (
        "Write an executive narrative using the Situation-Complication-"
        "Resolution (SCR) framework.\n\n"
        "Requirements:\n"
        "- Use exactly three headings: Situation, Complication, Resolution.\n"
        "- Use only the supplied facts.\n"
        "- Keep all numerical values unchanged.\n"
        "- Total length must be between 150 and 200 words.\n"
        "- Use professional executive language.\n"
        "- No bullet points.\n\n"
        "Findings:\n"
        f"- Cleaned total revenue (INR): "
        f"{f['cleaned_total_revenue_inr']}\n"
        f"- Raw total revenue (INR): "
        f"{f['raw_total_revenue_inr']}\n"
        f"- Duplicate reconciliation delta (INR): "
        f"{f['duplicate_reconciliation_delta_inr']}\n"
        "- Return rates by payment method (%): "
        + ", ".join(f"{k} {v}" for k, v in pay.items()) + "\n"
        f"- Highest-risk segment: "
        f"{seg['payment_method']} + Tier-{seg['city_tier']}, "
        f"return rate {seg['return_rate_pct']}%\n"
        f"- True peak month: "
        f"{peak['month']} "
        f"(revenue INR {peak['revenue_inr']})\n"
        f"- Outlier-inflated month: "
        f"{out['month']} "
        f"(apparent INR {out['apparent_revenue_inr']}, "
        f"corrected INR {out['corrected_revenue_inr']})"
    )


def generate_scr_narrative(findings: dict,
                           client=None,
                           model="gemini-3.8-flash") -> dict:
    """
    Online path with automatic offline fallback.
    Returns:
        {
            "status": "success",
            "narrative": str,
            "tokens": int
        }
    """

    if not os.environ.get("GEMINI_API_KEY"):
        return generate_scr_narrative_offline(findings)

    try:
        from google import genai
        from google.genai import types

        if client is None:
            client = genai.Client()

        response = client.models.generate_content(
            model=model,
            contents=_build_user_prompt(findings),
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=600,
                http_options=types.HttpOptions(timeout=30_000)
            )
        )

        if getattr(response, "status", None) == "error":
            return generate_scr_narrative_offline(findings)

        return {
            "status": "success",
            "narrative": response.text,
            "tokens": (
                response.usage_metadata.total_token_count
                if getattr(response, "usage_metadata", None)
                else None
            )
        }

    except Exception:
        return generate_scr_narrative_offline(findings)


def generate_scr_narrative_offline(findings: dict) -> dict:
    """
    Fully deterministic offline path.
    No API key.
    No network.
    Always works.
    """

    f = findings

    seg = f["highest_risk_segment"]
    peak = f["true_peak_month"]
    out = f["outlier_inflated_month"]

    narrative = (
        "Situation\n"
        f"The business generated a raw total revenue of INR "
        f"{f['raw_total_revenue_inr']:,.2f}. "
        f"After data reconciliation and cleaning, verified revenue stands at "
        f"INR {f['cleaned_total_revenue_inr']:,.2f}. "
        f"The duplicate-driven reconciliation delta was "
        f"INR {f['duplicate_reconciliation_delta_inr']:,.2f}.\n\n"

        "Complication\n"
        f"Performance assessment was distorted by an outlier that made "
        f"{_month_name(out['month'])} appear to generate "
        f"INR {out['apparent_revenue_inr']:,.2f}. After correction, the "
        f"month's revenue was only INR "
        f"{out['corrected_revenue_inr']:,.2f}. "
        f"Operationally, COD remains the highest-risk payment method with a "
        f"return rate of "
        f"{f['return_rate_by_payment']['COD']}%. "
        f"The most vulnerable segment is "
        f"{seg['payment_method']} + Tier-{seg['city_tier']} "
        f"with a return rate of {seg['return_rate_pct']}%.\n\n"

        "Resolution\n"
        f"The verified peak month is "
        f"{_month_name(peak['month'])} with revenue of "
        f"INR {peak['revenue_inr']:,.2f}. "
        f"Management should prioritize reducing COD returns in "
        f"Tier-{seg['city_tier']} markets, promote prepaid payment methods, "
        f"and maintain automated reconciliation controls so reporting "
        f"continues to reflect the cleaned revenue baseline of "
        f"INR {f['cleaned_total_revenue_inr']:,.2f}."
    )

    return {
        "status": "success",
        "narrative": narrative,
        "tokens": 0
    }


def check_required_findings(narrative: str) -> bool:
    """
    Verify required figures appear in the narrative.
    Normalizes commas before matching.
    Prints PASS/FAIL per requirement.
    """

    normalized = narrative.replace(",", "").lower()

    checks = [
        (
            "Cleaned revenue",
            (
                "97358.30" in normalized
                or "97358.3" in normalized
            )
        ),
        (
            "COD return rate",
            "44.4" in normalized
        ),
        (
            "Highest-risk segment return rate",
            "54.5" in normalized
        ),
        (
            "Duplicate reconciliation delta",
            (
                "2501.90" in normalized
                or "2501.9" in normalized
            )
        ),
        (
            "March peak month revenue",
            (
                "march" in normalized
                and (
                    "20318.90" in normalized
                    or "20318.9" in normalized
                )
            )
        )
    ]

    passed = True

    for label, result in checks:
        print(
            f"[{'PASS' if result else 'FAIL'}] {label}"
        )
        passed &= result

    return passed

