import json

from google import genai
from google.genai import types

SYSTEM_INSTRUCTION = """\
You are a senior data analyst writing for Mamaearth's regional ops and finance heads.

Structure
Write exactly three labeled sections, in this order, using these exact labels:
  Situation: what the data shows about current performance, stated plainly.
  Complication: what is going wrong, at risk, or unexplained, and why it matters.
  Resolution: the specific actions the findings support, with owners or regions where the findings name them.

Number integrity (hard constraint)
- Every number in your output (counts, percentages, currency amounts, dates, rankings) must come from the findings supplied in the user message and must appear with the same value and units. Do not round, convert, or reformat in a way that changes the value.
- Do not invent statistics, benchmarks, forecasts, or comparisons. Do not compute new figures (sums, differences, growth rates) unless that figure is itself present in the findings.
- If the findings do not support a point, say the data does not cover it instead of filling the gap.

Style
Concise, decision-oriented prose for senior business readers. No preamble before the Situation section and no text after the Resolution section.
"""


def generate_narrative(
    findings: dict,
    client: genai.Client | None = None,
    model: str = "gemini-2.5-flash",
) -> dict:
    """Turn a findings dict (e.g. loaded from findings.json) into a
    Situation / Complication / Resolution narrative.

    Never raises. Returns:
      {"status": "success", "narrative": str, "tokens": int}
      {"status": "error",   "narrative": None, "message": str}
    """
    try:
        if not findings:
            raise ValueError("findings is empty; nothing to narrate.")

        client = client or genai.Client()  # reads GEMINI_API_KEY / GOOGLE_API_KEY from env

        # All numbers reach the model only through this interpolated block.
        findings_block = json.dumps(findings, indent=2, ensure_ascii=False)
        contents = (
            "Write the Situation, Complication, Resolution narrative based solely on "
            "the findings below. Use only numbers that appear in them.\n\n"
            f"<findings>\n{findings_block}\n</findings>"
        )

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                # temperature=0.0: this is a factual business report, not creative
                # writing. We want deterministic output that stays pinned to the
                # supplied figures, not varied or "inventive" phrasing of them.
                temperature=0.0,
                # Explicit cap (not the API default). A 3-section, ~250-word
                # narrative needs roughly 350-400 tokens; 1024 leaves headroom,
                # including for any thinking tokens, which count toward this limit.
                max_output_tokens=1024,
                # Request timeout in milliseconds (30 s, above the 10 s minimum).
                http_options=types.HttpOptions(timeout=30_000),
            ),
        )

        if not response.text:
            raise RuntimeError("Model returned no text (possibly blocked or empty response).")

        usage = response.usage_metadata
        return {
            "status": "success",
            "narrative": response.text,
            "tokens": usage.total_token_count if usage else None,
        }

    except Exception as err:  # noqa: BLE001 - caller must never receive a raw exception
        return {"status": "error", "narrative": None, "message": str(err)}


if __name__ == "__main__":
    with open("findings.json", encoding="utf-8") as f:
        print(generate_narrative(json.load(f)))
