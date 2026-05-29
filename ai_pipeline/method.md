# How to Build an AI Agent Data Investigation Pipeline

A reusable blueprint for turning a large public dataset into an AI-powered
investigation workshop — applicable to any domain, not just food.

---

## The Big Picture

```
┌──────────────────────────────────────────────────────┐
│  ASSIGNMENTS        What story are we telling?       │
│  (Markdown)         Hypothesis → Task definition     │
└──────────┬───────────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────────┐
│  SKILL              How does the agent access data?  │
│  (SKILL.md)         Schema, query patterns, rules,   │
│                     visualisation standards, caveats  │
└──────────┬───────────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────────┐
│  SCRIPTS            The programmatic engine           │
│  (Python)           Data wrapper, HTML generator,    │
│                     download/split utilities          │
└──────────┬───────────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────────┐
│  DATA               The raw material                 │
│  (Parquet/SQLite)   Local columnar file, pre-loaded  │
└──────────┬───────────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────────┐
│  OUTPUT             The deliverable                  │
│  (HTML)             Self-contained report, served    │
│                     statically via reverse proxy      │
└──────────────────────────────────────────────────────┘
```

The pipeline is **five layers**, each with a single responsibility.
The AI agent (Claude, GPT, etc.) sits between Assignments and Scripts:
it reads the task, loads the skill for domain knowledge, then calls
scripts to query data and produce output.

---

## Layer 1 — Assignments (The "What")

Assignments are plain Markdown files that define the investigation.
They say **what** to find, not **how** to find it.

### Why separate assignments from code?

- Journalists/editors can write assignments without touching code
- The same skill can serve multiple assignments
- Assignments can be customised per user (add country, brand, hypothesis)
- The agent picks up any context added to the assignment file

### Template

```markdown
# Assignment [Letter] — [Story Title] · Part [N]: [Subtitle]

> One-paragraph hook: the paradox, the claim, the surprise.

## The investigation

[2-3 sentences describing the analytical approach.]

**Suggested angles to investigate:**

| Dimension A | Dimension B | What to look for |
|---|---|---|
| [Group 1] | [Group 2] | [Expected contrast] |

## Part [N] — [Focus] *(~[time estimate])*

Tell your agent:

> *"Concrete instruction quoting the skill methods and
>   specifying the output format."*

**What to look for:** [Specific patterns, outliers, paradoxes.]

## Sharpen your angle

[Placeholders the user can edit before running the agent:
 country, brand, specific product, headline hypothesis.]

---

*Data: [Dataset Name] ([License]) — include attribution in your output.*
*Skill: `skills/[skill-name]/SKILL.md`*
```

### Key principles

1. **Start with a hook** — the paradox or surprise that makes this a story
2. **Give concrete agent instructions** — a quoted prompt the user can paste
3. **Suggest but don't prescribe** — "Pick one pair or all of them"
4. **Make it editable** — users add their own angle before running
5. **Chain parts** — Part 1 gives a solid finding; Part 2 goes deeper
6. **Always require attribution** — data licence compliance

---

## Layer 2 — The Skill (The "How")

The skill is a single `SKILL.md` file that makes the AI agent a domain
expert. It is the most critical piece of the architecture.

### Why a skill file?

- LLMs don't know your schema, your query dialect, or your caveats
- A skill file is **loaded automatically** when the task matches
- It replaces thousands of dollars of prompt engineering with a
  copy-pasteable Markdown file
- It encodes institutional knowledge (coverage gaps, broken column
  names, visualisation rules) that would otherwise be lost

### SKILL.md structure

```yaml
---
name: your-domain
description: >
  Trigger keywords and purpose statement.
  The agent framework matches task descriptions against this
  to decide when to load the skill.
---
```

Followed by these sections (in order):

| Section | Purpose | Must include |
|---|---|---|
| **Purpose** | What the skill does, in one paragraph | Dataset name, licence, key capability |
| **Data file** | Where the data lives, how to load it | File path, loading code, row count |
| **Two access modes** | Primary (bulk) vs. secondary (per-item) | When to use which, rate limits |
| **Quick-reference files** | What to read for what need | File → purpose table |
| **Workflow (primary)** | Step-by-step data access pattern | 7 steps (see below) |
| **Schema reference** | The columns that matter | Identity, geography, classification, scores, timestamps |
| **Domain concepts** | What the scores/tags/classifications mean | Coverage rates, caveats |
| **Coverage caveats** | What's missing, what's biased | Always report these |
| **Data ethics & attribution** | Required credit line | Exact string to include |
| **Visualisation** | Chart types, colours, principles | Goal → chart type table, colour dicts |
| **Output format** | What every investigation must produce | 5-point checklist |
| **HTML design system** | CSS framework for outputs | Token palette, dark mode, fonts |
| **Showcase trigger** (optional) | Fast-track brand/topic analysis | Step-by-step generator flow |

### The 7-step workflow pattern

This is the generic pipeline the agent follows for any investigation:

```
Step 1: Locate the data file
        → Pre-downloaded? If not, run download script.

Step 2: Install dependencies
        → pip install [db-driver] [dataframe-lib] [viz-lib]

Step 3: Import and connect
        → from wrapper import DataClass
        → data = DataClass("path/to/data.parquet")

Step 4: Explore the schema first
        → data.info(), data.sample(3), data.schema()
        → NEVER skip this step.

Step 5: Choose your query approach
        → Built-in method? Custom SQL? API lookup?
        → Decision table: investigation → method.

Step 6: Run the analysis
        → All methods return DataFrames.
        → Validate: n, coverage rate, sample rows.

Step 7: Visualise findings
        → Journalism-style titles (finding, not description).
        → Sample size annotation. Attribution.
```

### The JavaScript safety rule

When injecting Python values into HTML `<script>` blocks, **always**
use `json.dumps()`. Brand names with apostrophes ("Kellogg's"), special
characters, or non-ASCII text will break JS string literals.

```python
# BROKEN
label: '{brand}'

# CORRECT
label: {json.dumps(brand)}
```

This applies to **every** f-string that touches `<script>`.

---

## Layer 3 — Scripts (The Engine)

Four Python scripts form the reusable core. Adapt the data layer for
your domain; the HTML generator follows a universal pattern.

### 3a — Data wrapper (`data_wrapper.py`)

The central class that wraps your database and provides domain methods.

```python
class DomainData:
    """Wraps a local Parquet/SQLite file with DuckDB/SQL queries."""

    PARQUET_URL = "https://[your-dataset-download-url]"
    ATTRIBUTION = "Data: [Source] ([url]), [licence]"

    def __init__(self, path: str):
        """Connect to the local data file."""
        # 1. Open DuckDB connection
        # 2. Load the parquet as a view/table
        # 3. Print confirmation with row count

    # ── Schema exploration ──────────────────────────
    def info(self) -> None:            # Print dataset overview
    def schema(self) -> str:           # Full column list with types
    def sample(self, n: int = 3):      # Random sample rows

    # ── Domain-specific methods ────────────────────
    # Each returns a pandas DataFrame.
    # Each accepts country/filter params.
    # Each logs the query and row count.

    def distribution_x(self, country=None, category=None) -> pd.DataFrame:
    def distribution_y(self, country=None, category=None) -> pd.DataFrame:
    def comparison(self, items, country=None) -> pd.DataFrame:
    def gaps(self, country=None) -> pd.DataFrame:
    def search(self, term, country=None) -> pd.DataFrame:

    # ── Custom queries ──────────────────────────────
    def query(self, sql: str) -> pd.DataFrame:
        """Run arbitrary SQL. The escape hatch."""

    # ── Export ──────────────────────────────────────
    def export_subset(self, sql: str, path: str) -> Path:
        """Save query results as a new parquet."""

    @staticmethod
    def attribution() -> str:
        return DomainData.ATTRIBUTION
```

**Design principles for the wrapper:**

1. **Every method returns a DataFrame** — the agent can inspect, filter, chart
2. **Every method logs its query and row count** — auditability
3. **The `.query(sql)` escape hatch exists** — the agent isn't limited to built-in methods
4. **Country/filter params are consistent** — same keyword argument pattern everywhere
5. **Attribution is a static method** — every chart footer can call it
6. **Schema exploration is step 1** — the agent never guesses column names

### 3b — HTML showcase generator (`showcase.py`)

Generates a self-contained HTML page for a topic/brand/entity.

```python
def generate_showcase(
    entity: str,
    data_path: str,
    output_dir: str = "output",
) -> Path:
    """Generate an HTML profile page for [entity].

    Sections:
      1. Hero stats (count, key metric, worst/best indicator)
      2. Distribution chart (primary score)
      3. Distribution chart (secondary score)
      4. Comparison vs. category average
      5. Top sub-categories
      6. Flagged items table
      7. Best items table
      8. Worst items table

    Returns: path to the saved HTML file.
    """
```

**Key rules for the generator:**

- **Self-contained HTML** — all CSS, JS, data inline. No server needed.
- **Design system CSS** — copy from `design/SKILL.md`, don't invent ad-hoc styles
- **`json.dumps()` for all JS injections** — never interpolate raw strings
- **Finding-based chart titles** — "One in three X is Y", not "Distribution of Y in X"
- **Sample size + attribution in every chart**

### 3c — Download script (`download_data.py`)

Simple idempotent downloader.

```python
def download(data_dir: str) -> Path:
    """Download the main data file. Skips if already present."""
    # 1. Check if file exists → skip
    # 2. Stream-download with progress bar
    # 3. Print size and time
```

### 3d — Split script (`split_data.py`)

Optional: splits the big file into per-country/per-dimension subsets
for faster queries and lower RAM usage.

```python
def split(data_path: str, output_dir: str) -> list[Path]:
    """Split the main parquet into subset files."""
    # 1. Query distinct values of the split dimension (e.g. countries)
    # 2. For each: FILTER + COPY
    # 3. Write manifest.json with row counts and sizes
```

---

## Layer 4 — Data (The Raw Material)

### Format choice

| Format | Best for | Trade-off |
|---|---|---|
| **Parquet** | Columnar analytics, millions of rows, DuckDB queries | Need DuckDB/PyArrow; not human-readable |
| **SQLite** | Row-oriented lookups, moderate size, JOIN-heavy | Slower for aggregations; easier to inspect |
| **CSV** | Small datasets, human inspection | No type safety, slow for >1M rows |

**For datasets >1M rows: Parquet + DuckDB.** This is the non-negotiable
core of the architecture. DuckDB queries 4.5M rows in under a second,
entirely locally, no database server needed.

### Data provisioning

The data must be available **before** the agent starts. Three strategies:

| Strategy | How | When to use |
|---|---|---|
| **Pre-baked VM image** | Data included in the VM snapshot | Workshop/event setup |
| **systemd one-shot service** | Downloads on first boot, marks `.done` | Cloud VM provisioning |
| **Manual download** | Agent runs `download_data.py` if file missing | Development / ad-hoc |

The systemd pattern:

```ini
[Unit]
Description=Download [dataset] data
After=network-online.target
ConditionPathExists=!/home/user/data/.done

[Service]
Type=oneshot
ExecStart=/path/to/prepare_data.sh
ExecStartPost=/bin/touch /home/user/data/.done
TimeoutStartSec=3600
```

### Schema considerations

Regardless of domain, these column patterns recur:

| Pattern | Example | DuckDB pattern |
|---|---|---|
| **Multi-value tags** (array) | `countries_tags`, `categories_tags` | `list_contains(col, 'en:france')` |
| **Multilingual structs** | `product_name: STRUCT(lang, text)[]` | `list_transform(col, x -> x."text")` |
| **Nested nutriments/metrics** | `nutriments: STRUCT(name, value)[]` | `list_extract(list_filter(col, x -> x.name = 'sugars'), 1).value` |
| **Sparse scores** (lots of NULLs) | `nutriscore_grade` (40-50% coverage) | Always report `COUNT(col) / COUNT(*)` |
| **Messy free-text fields** | `brands`, `stores` | `LOWER(brands) LIKE '%nestl%'` |

---

## Layer 5 — Output (The Deliverable)

### Self-contained HTML

Every investigation produces a single HTML file:

```
output/
└── investigation-name.html    ← CSS + JS + data, all inline
```

No build step, no server, no framework. Opens in any browser.

### Why not a Jupyter notebook?

- **Shareability** — send a link, not a `.ipynb` + requirements.txt
- **No execution environment needed** — the reader doesn't need Python
- **Static hosting** — Caddy/nginx serves it directly
- **Print/PDF** — journalists can screenshot or print

### The design system pattern

Don't invent CSS per report. Define a **design skill** once:

```markdown
# skills/design/SKILL.md

## CSS base (copy into <head>)
:root {
  --bg: #fafafa; --fg: #18181b; --border: #e4e4e7;
  --font-sans: 'Inter', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --radius: 4px;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #09090b; --fg: #fafafa; --border: #27272a; }
}
/* ... component classes: .stats, .stat, table.data, .mono ... */
```

Every HTML output pastes this CSS base and uses the token variables.
**No Bootstrap, no Tailwind, no ad-hoc hex colours.**

### Chart rendering options

| Approach | Pros | Cons |
|---|---|---|
| **Plotly (Python → inline JS)** | Interactive, hover, zoom | Heavy (~1MB JS) |
| **Chart.js (inline data)** | Lightweight, flexible | More manual JS |
| **SVG only (matplotlib → embed)** | Zero JS, print-perfect | Not interactive |
| **Observable Plot** | Clean API, notebook-native | Needs ES module import |

For journalism: **Plotly or Chart.js** with finding-based titles.

---

## The Agent Integration

### How the agent decides what to do

```
1. User prompt arrives
2. Agent framework matches against skill descriptions
3. Matching skill's SKILL.md is loaded into context
4. Assignment file is read (if referenced)
5. Agent follows the 7-step workflow from the skill
6. Agent calls scripts/off_parquet.py methods
7. Agent builds HTML output using design/SKILL.md CSS
8. Agent saves to ~/output/ and verifies the URL
```

### What the agent needs in its system prompt

```
- Working directory (~/workshop)
- Data directory (~/data/[domain])
- Output directory (~/output)
- Static URL prefix (https://<vm>/output/)
- Skill locations (~/workshop/skills/)
- Tool availability (pi, duckdb, python, etc.)
```

### The skill auto-load mechanism

Skills have YAML frontmatter with a `description` field containing trigger
keywords. When the user's prompt matches (e.g. "Nutri-Score", "NOVA",
"food data"), the framework loads the corresponding SKILL.md.

**For your own domain:** add 10-15 trigger keywords that a user might
naturally say when they need your data.

---

## Adapting This to a New Domain

### Step-by-step

| Step | What to do | Time |
|---|---|---|
| **1. Get the data** | Find a public dataset. Download as Parquet or convert (CSV → Parquet with DuckDB: `COPY (SELECT * FROM read_csv('data.csv')) TO 'data.parquet'`) | 1-2 hours |
| **2. Write the wrapper** | Create `data_wrapper.py` following the class template. Start with `.info()`, `.schema()`, `.sample()`, `.query()`. Add domain methods as needed. | 2-4 hours |
| **3. Write the SKILL.md** | Document schema, query patterns, caveats, visualisation rules. This is the biggest intellectual investment — it's what makes the agent smart. | 3-6 hours |
| **4. Write assignments** | Define 1-2 investigation stories. Start with the paradox/surprise. Give concrete agent prompts. | 1-2 hours |
| **5. Build the showcase generator** | Adapt `brand_showcase.py` for your entity type. 8 sections: hero, 2x distributions, comparison, top-X, flagged, best, worst. | 3-4 hours |
| **6. Define the design system** | Copy `design/SKILL.md`, adjust colours/tokens for your domain if needed. Usually the zinc palette works universally. | 30 min |
| **7. Set up provisioning** | `download_data.py` + optional `split_data.py` + systemd service. | 1-2 hours |
| **8. Test with the agent** | Run the assignment. Iterate on the skill file based on what the agent gets wrong. | 2-4 hours |

### Choosing a good domain

The architecture works best when:

- ✅ The dataset is **large** (>100K rows — DuckDB shines)
- ✅ The data has **scores or classifications** that can contradict each other
- ✅ There are **paradoxes or surprises** (the Mediterranean Trap pattern)
- ✅ Coverage is **incomplete** (missing data is itself a story)
- ✅ The data has **categorical tags** (for filtering and grouping)
- ✅ Results need **visual storytelling** (not just tables)

Examples: property prices vs. flood risk, car safety ratings vs. real-world
crash data, university rankings vs. graduate outcomes, air quality
measurements vs. industrial zoning.

---

## File Tree Template

```
project/
├── assignments/
│   ├── README.md                       # Investigation overview
│   └── a-story-name/
│       ├── assignment-part-1.md        # Core finding
│       └── assignment-part-2.md        # Deeper analysis
├── skills/
│   ├── [domain]/
│   │   ├── SKILL.md                    # The brain (500+ lines)
│   │   ├── scripts/
│   │   │   ├── data_wrapper.py         # Data class (the heart)
│   │   │   ├── showcase.py             # HTML generator
│   │   │   ├── download_data.py        # Idempotent downloader
│   │   │   ├── split_data.py           # Subset creator
│   │   │   └── requirements.txt
│   │   └── references/
│   │       ├── story-recipes.md         # Query pattern library
│   │       ├── methodology-reference.md # How scores work
│   │       └── api-guide.md            # Secondary data source
│   └── design/
│       └── SKILL.md                    # CSS design system
├── scripts/
│   └── prepare_data.sh                # VM provisioning script
├── systemd/
│   └── data-prep.service              # First-boot data download
├── data/                               # ← gitignored, >1GB
│   ├── main.parquet
│   ├── subset_foo.parquet
│   ├── manifest.json
│   └── .done
├── output/                             # ← gitignored, generated
│   └── investigation.html
├── START_HERE.md
└── AGENTS.md                           # Agent system prompt context
```

---

## The Three Laws of This Architecture

1. **The skill is the spec.** If it's not in SKILL.md, the agent doesn't
   know it. Schema quirks, broken column names, coverage gaps — write them
   down. Every hour of SKILL.md writing saves ten hours of agent debugging.

2. **Local data, not API.** The whole point is sub-second queries on
   millions of rows. Download once, query locally. APIs are for single-item
   lookups only.

3. **Self-contained output.** Every deliverable is one HTML file. No build
   step, no runtime, no framework. If the server goes down, the file still
   opens in a browser.
