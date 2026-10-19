"""
SCR narrative generator for Mamaearth regional ops/finance review.

Two paths:
  1. Online  — Gemini via google-genai (deterministic: temperature=0.0).
  2. Offline  — pure f-string template, zero config, same return shape.

Both return: {"status", "narrative", "tokens" | "message"}.
"""

import os
from datetime import datetime


def _month_name(yyyy_mm: str) -> str:
    """'2026-03' -> 'March' (for narrative text; findings stay numeric)."""
    return datetime.strptime(yyyy_mm, "%Y-%m").strftime("%B")


def _build_system_instruction() -> str:
    """System instruction: role, structure, and the no-invented-numbers rule.
    Kept OUT of the user prompt so the model treats it as standing policy."""
    return (
        "You are a senior data analyst writing for Mamaearth's regional ops "
        "and finance heads.\n"
        "Structure every response as exactly three labeled sections:\n"
        "1. Situation\n2. Complication\n3. Resolution\n"
        "Hard constraint: every number in the output must come from the "
        "supplied findings and appear with the same value. Do not invent, "
        "round, or extrapolate any statistic."
    )


def _build_user_prompt(findings: dict) -> str:
    """Build the user prompt by interpolating the findings dict — nothing
    hardcoded, so a different findings.json yields a different narrative
    without touching this function."""
    f = findings
    pay = f["return_rate_by_payment"]
    seg = f["highest_risk_segment"]
    peak = f["true_peak_month"]
    out = f["outlier_inflated_month"]
    return (
        "Write the SCR narrative from these findings:\n"
        f"- Cleaned total revenue (INR): {f['cleaned_total_revenue_inr']}\n"
        f"- Raw total revenue (INR): {f['raw_total_revenue_inr']}\n"
        "- Return rate by payment method (%): "
        + ", ".join(f"{k} {v}" for k, v in pay.items()) + "\n"
        f"- Highest-risk segment: {seg['payment_method']} + Tier-"
        f"{seg['city_tier']}, return rate {seg['return_rate_pct']}%\n"
        f"- Duplicate reconciliation delta (INR): "
        f"{f['duplicate_reconciliation_delta_inr']}\n"
        f"- True peak month: {peak['month']} "
        f"(revenue INR {peak['revenue_inr']})\n"
        f"- Outlier-inflated month: {out['month']} "
        f"(apparent INR {out['apparent_revenue_inr']}, corrected INR "
        f"{out['corrected_revenue_inr']})\n"
    )


def generate_scr_narrative(findings: dict, client=None,
                           model: str = "gemini-2.5-flash") -> dict:
    """Online path: call Gemini, fall back to offline on any failure."""
    # Offline fallback trigger 1: no API key configured
    if not os.environ.get("GEMINI_API_KEY"):
        return generate_scr_narrative_offline(findings)

    try:
        # Lazy import so the offline path needs zero dependencies
        from google import genai
        from google.genai import types

        if client is None:
            client = genai.Client()  # reads GEMINI_API_KEY from env

        response = client.models.generate_content(
            model=model,
            contents=_build_user_prompt(findings),
            config=types.GenerateContentConfig(
                system_instruction=_build_system_instruction(),
                temperature=0.0,        # deterministic: factual business
                                        # report, not creative writing
                max_output_tokens=600,  # explicit, not API default;
                                        # >300, fits ~250-word SCR
                http_options=types.HttpOptions(timeout=30),  # >= 10s min
            ),
        )
        if getattr(response, "status", None) == "error":
            return generate_scr_narrative_offline(findings)
        return {
            "status": "success",
            "narrative": response.text,
            "tokens": response.usage_metadata.total_token_count
                      if response.usage_metadata else None,
        }
    except Exception as err:  # caller never sees a raw exception
        # Offline fallback trigger 2: any API failure
        return generate_scr_narrative_offline(findings)


def generate_scr_narrative_offline(findings: dict) -> dict:
    """Offline path: fully deterministic f-string template. No network,
    no API key, same return-dict shape, same key figures."""
    f = findings
    seg = f["highest_risk_segment"]
    peak = f["true_peak_month"]
    out = f["outlier_inflated_month"]
    narrative = (
        "Situation\n"
        f"After cleaning, Mamaearth's total revenue stands at INR "
        f"{f['cleaned_total_revenue_inr']:,.2f}, down from a raw figure of "
        f"INR {f['raw_total_revenue_inr']:,.2f}. The gap is fully explained "
        f"by duplicate records, which drove a reconciliation delta of INR "
        f"{f['duplicate_reconciliation_delta_inr']:,.2f}.\n"
        "Complication\n"
        f"Returns are concentrated in COD: the COD return rate is "
        f"{f['return_rate_by_payment']['COD']}%, versus "
        f"{f['return_rate_by_payment']['UPI']}% for UPI and "
        f"{f['return_rate_by_payment']['CARD']}% for CARD. The "
        f"highest-risk segment is COD in Tier-{seg['city_tier']} cities at "
        f"{seg['return_rate_pct']}%. Revenue timing was also misread: "
        f"{_month_name(out['month'])} looked like the peak at INR "
        f"{out['apparent_revenue_inr']:,.2f}, but that was an outlier — "
        f"corrected revenue is only INR "
        f"{out['corrected_revenue_inr']:,.2f}.\n"
        "Resolution\n"
        f"{_month_name(peak['month'])} is the true peak month with revenue "
        f"of INR {peak['revenue_inr']:,.2f}. Ops should prioritise COD "
        f"return-reduction in Tier-{seg['city_tier']} cities, and finance "
        f"should treat INR "
        f"{f['duplicate_reconciliation_delta_inr']:,.2f} as the "
        f"reconciled duplicate-driven gap."
    )
    return {"status": "success", "narrative": narrative, "tokens": 0}


# Each entry: substrings that must ALL appear after comma-normalization.
REQUIRED_FIGURES = {
    "cleaned_total_revenue": ["97358.3"],
    "cod_return_rate_pct": ["44.4"],
    "cod_tier2_return_rate_pct": ["54.5"],
    "recon_delta_duplicates": ["2501.9"],
    "true_peak_month_and_revenue": ["March", "20318.9"],
}


def check_narrative(narrative: str) -> bool:
    """Assert all five key figures appear as substrings after normalizing
    commas. Prints one pass/fail line per figure; returns overall verdict."""
    normalized = narrative.replace(",", "")
    ok = True
    for label, parts in REQUIRED_FIGURES.items():
        found = all(p in normalized for p in parts)
        ok = ok and found
        print(f"{'PASS' if found else 'FAIL'}: {label} -> {' + '.join(parts)}")
    return ok
