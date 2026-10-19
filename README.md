# ArbadCapsProj — Orders Analysis: SQL → Python EDA → Executive Narrative

An end-to-end analysis of a small e-commerce orders dataset for Mamaearth(45 customers, 16 products, 180 raw orders, Jan–Jun 2026):

1. **SQL** – build the database and run the Part 1 reports.
2. **Python analysis** – clean the data, run EDA/hypothesis tests, draw two charts, export `findings.json`.
3. **Narrator** – turn `findings.json` into a 150–200-word Situation-Complication-Resolution (SCR) summary, either with the Gemini API or fully offline.


## Repository layout
```
sql/
  schema.sql              # CREATE TABLE statements (customers, products, orders)
  seed_data.sql           # INSERTs for the three tables
  reports.sql             # Part 1 reports (a)–(i)
data/
  customers.csv  products.csv  orders.csv   # same data, as CSV, for pandas
analysis/
  clean_and_eda.py        # cleaning, reconciliation, outliers, hypothesis tests
  visualize.py            # 2 PNG charts + writes narrator/findings.json
narrator/
  findings.json           # input to the narrator (generated at the end of visualize.py)
  generate_narrative.py   # online (Gemini) path + offline fallback
  sample_output.txt       # example of a Gemini-written narrative
```


## Prerequisites

- Python 3.10+ (tested on 3.12) and SQLite 3 (`sqlite3` command-line shell)
- Python packages:

```bash
git clone https://github.com/Arbad12/ArbadCapsProj.git
cd ArbadCapsProj

pip install pandas matplotlib          # required for steps 2 and 3
pip install google-genai               # optional: only for the Gemini (online) path in step 3
```

All commands below are run from the repository root unless a `cd` is shown. The Python scripts use relative paths (`../data/...`), so **run them from inside their own folder** exactly as shown.

---

## 1. SQL: load the schema and seed data, then run the reports

The SQL was verified with SQLite 3. From the repository root:

```bash
# 1a. Create an empty database and load schema, then seed data (order matters)
sqlite3 arbad.db < sql/schema.sql
sqlite3 arbad.db < sql/seed_data.sql

# 1b. Sanity check – expect 45, 16, 180
sqlite3 arbad.db "SELECT COUNT(*) FROM customers; SELECT COUNT(*) FROM products; SELECT COUNT(*) FROM orders;"

# 1c. Run all reports
sqlite3 -header -column arbad.db < sql/reports.sql
```

> Re-running from scratch? Delete the database first (`rm arbad.db`), because `schema.sql` uses plain `CREATE TABLE` and report (i) alters `customers`.

Expected results (also written as comments inside `reports.sql`):

| Report | Result |
|---|---|
| (a) total orders / total revenue / avg order value | 180 / **99,860.20** / 554.78 |
| (b) `COUNT(*)` vs `COUNT(rating)` | 180 / 165 / 15 missing ratings |
| (c) customers with zero orders | C045 Vihaan |
| (d) return rate by city, only cities > 20% | Jaipur 42.1% (8/19), Lucknow 30.6% (15/49), Bangalore 24.2% (8/33) |
| (e) top-5 customers by spend | Reyansh 12,920.0; Isha 8,371.6; Meera 4,564.6; Arjun 4,111.0; Sanya 3,785.0 (OFFSET query returns ranks 3–5) |
| (f) revenue by category | Haircare 44,956.1; Skincare 27,346.0; Babycare 16,805.0; PersonalCare 10,753.1 |
| (g) names starting with "A" | 10 customers |
| (h) distinct acquisition sources | Organic, Referral, Ad, Social |
| (i) loyalty tier after `ALTER` + `UPDATE` | Gold 28, Silver 17 |

Revenue everywhere is `quantity × price × (1 − discount_pct/100)`, with a missing discount treated as 0.

**Important:** the figure **99,860.20** is the *raw* revenue — it still includes 5 duplicate order rows. Step 2 removes them.

---

## 2. Python analysis: clean, explore, visualise

Run the scripts **in this order**, from inside `analysis/`:

```bash
cd analysis

# 2a. Clean + EDA – prints every cleaning/EDA number
python clean_and_eda.py

# 2b. Charts + findings.json (re-runs 2a internally, then plots)
python visualize.py
```

- `visualize.py` imports its inputs from `clean_and_eda.py`, so 2a is also executed when you run 2b. Running 2a on its own first is just for readability of the console output.
- `visualize.py` opens two chart windows (`plt.show()`); close each to continue. On a server/headless machine, avoid windows with:
  `MPLBACKEND=Agg python visualize.py`

**Outputs created**

| File | What it is |
|---|---|
| `analysis/return_rate_by_payment.png` | Bar chart: return rate by payment method |
| `analysis/monthly_revenue_trend.png` | Line chart: outlier-corrected monthly revenue |
| `narrator/findings.json` | The numbers handed to the narrator in step 3 |

**What `clean_and_eda.py` does and the numbers it should print**

| Step | Result |
|---|---|
| Load | `orders` shape (180, 9) |
| Standardise `payment_method` (`upi/UPI/Card/cod/...` → upper case) | CARD 70, UPI 55, COD 55 |
| Remove duplicate orders (all columns except `order_id`) | dropped `O0176–O0180`; 175 rows remain |
| Impute | `discount_pct` nulls (12) → 0; `rating` nulls (15) → median **3.0** |
| Cleaned total revenue | **₹97,358.30** |
| Reconciliation vs SQL report (a) | raw ₹99,860.20 − cleaned ₹97,358.30 = **₹2,501.90** (= value of the 5 dropped duplicates) |
| IQR outliers on `quantity` (Q1=1, Q3=2, bounds −0.5 / 3.5) | `O0011` (qty 25), `O0098` (qty 30) |
| Return rate by payment method | **COD 44.4%**, UPI 18.9%, CARD 14.7% → hypothesis "COD returns more" **confirmed** |
| Payment × city-tier | highest-risk segment **COD + Tier-2 = 54.5%** (COD T1 37.5%, CARD T2 26.1%, UPI T1 19.4%, UPI T2 18.2%, CARD T1 8.9%) |
| Correlations | all pairs "negligible" (|r| < 0.20); discount vs returned r = −0.09 → hypothesis "discounts reduce returns" **busted** |
| Monthly revenue, raw | Jan 29,582.1 · Feb 13,195.5 · Mar 20,318.9 · Apr 9,495.3 · May 13,151.1 · Jun 11,615.4 |
| Monthly revenue, outliers excluded | Jan **11,637.1** · … · **Mar 20,318.9 (true peak)** |

Take-away: January only *looks* like the best month because of the two bulk orders; once they are excluded, **March** is the real peak.

---

## 3. Narrator: generate the executive narrative

`narrator/generate_narrative.py` reads `narrator/findings.json` (created in step 2b; a copy is committed, so this step also works on its own) and writes a Situation / Complication / Resolution narrative, then self-checks that five required figures appear (cleaned revenue 97,358.3 · COD 44.4% · segment 54.5% · delta 2,501.9 · March 20,318.9).

Run it from inside `narrator/`:

```bash
cd ../narrator          # if you are still in analysis/
```

### 3a. Offline path — no API key, no network (deterministic)

Make sure no key is set, then run:

```bash
# macOS / Linux
unset GEMINI_API_KEY
python generate_narrative.py

# Windows PowerShell
Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
python generate_narrative.py
```

The script prints `Mode: offline (no API key)`, a template-built narrative (123 words, 0 tokens used), and five `[PASS]` lines. The output is identical on every run, so it is the version to use for exact reproduction.

### 3b. Online path — Gemini API key as an environment variable

Create a key in [Google AI Studio](https://aistudio.google.com/app/apikey) and export it as **`GEMINI_API_KEY`** (the name the script and the `google-genai` client both read). Never hard-code or commit the key.

```bash
# macOS / Linux (current shell only)
export GEMINI_API_KEY="your-key-here"
python generate_narrative.py

# Windows PowerShell (current session only)
$env:GEMINI_API_KEY = "your-key-here"
python generate_narrative.py

# Windows cmd
set GEMINI_API_KEY=your-key-here
python generate_narrative.py
```

With the key set, the script prints `Mode: online …` and sends the findings to Gemini (temperature 0, ≤ 600 output tokens, 30 s timeout) using the model set as the default `model=` argument of `generate_scr_narrative()`.

**Automatic fallback:** if the key is missing, `google-genai` is not installed, the model name is rejected, the call times out, or any error occurs, the script silently falls back to the offline narrative — so it never fails. If you set a key but still see 0 tokens and the template wording, the call fell back; check that `google-genai` is installed and that the model id is valid for your account.

**Offline vs online results:** the numbers in the narrative are identical in both modes (the five `[PASS]` checks enforce this). Only the wording differs, and Gemini's prose can vary slightly between runs. `narrator/sample_output.txt` is an example of an online-generated narrative.

---

## Quick reproduction (copy-paste)

```bash
git clone https://github.com/Arbad12/ArbadCapsProj.git && cd ArbadCapsProj
pip install pandas matplotlib

# 1. SQL
sqlite3 arbad.db < sql/schema.sql && sqlite3 arbad.db < sql/seed_data.sql
sqlite3 -header -column arbad.db < sql/reports.sql

# 2. Analysis
cd analysis && MPLBACKEND=Agg python visualize.py && cd ..

# 3. Narrator (offline)
cd narrator && python generate_narrative.py
```

## Headline numbers (all reproduced above)

| Metric | Value |
|---|---|
| Raw revenue (SQL report a, 180 orders) | ₹99,860.20 |
| Cleaned revenue (175 orders after removing 5 duplicates) | ₹97,358.30 |
| Duplicate reconciliation delta | ₹2,501.90 |
| Return rate — COD / UPI / Card | 44.4% / 18.9% / 14.7% |
| Highest-risk segment | COD + Tier-2 city, 54.5% |
| January revenue: apparent → outlier-corrected | ₹29,582.10 → ₹11,637.10 |
| True peak month | March 2026, ₹20,318.90 |
