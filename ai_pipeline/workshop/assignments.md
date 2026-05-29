# Assignment A — The Mediterranean Trap · Part 1: The Score Comparison

> Nutri-Score rates food on nutrients per 100g — but it doesn't care whether a food is
> natural or industrial.
> Coconut oil scores E despite being NOVA 2 (minimally processed).
> A flavoured oil spray full of additives scores B.
> Raw almonds score C while chemically-flavoured snack bars score A.
> Can you find these paradoxes with data?

---

## The investigation

Compare Nutri-Score grades for natural/traditional foods vs. their industrial counterparts,
then cross-reference with NOVA processing levels to reveal the paradox.

**Suggested pairs to investigate:**

| Natural food | Industrial counterpart | What to find |
|---|---|---|
| Olive oil / Coconut oil | Vegetable/sunflower oil blends | NOVA 2 oils scoring E vs NOVA 4 sprays scoring B |
| Nuts & almonds | Chips & crisps (`en:chips-and-fries`) | Almonds (A/B) vs chips (C/D) — nature wins here |
| Hard cheese (Parmesan, Manchego, Gruyère) | Processed cheese slices | NOVA 1/2 vs NOVA 4, Nutri-Score C/D for both |
| Cured ham / prosciutto | Deli meat / reformed ham | Real ham vs reformed ham: similar scores, very different processing |

Pick one pair or all of them.

---

## Part 1 — The score comparison *(~15 min)*

Tell your agent:

> *"Use the openfoodfacts skill to compare Nutri-Score distributions for olive oils vs. vegetable oils in France. Also compare NOVA groups for both. Show the full A–E grade breakdown for each category. Build a clean HTML page with a bar chart for each comparison and a headline finding."*

**Suggested focus:** France (`en:france`) has the most data. Swap in your own country if you prefer.

**What to look for:** Olive oils score mostly B — similar to industrial blends. The story isn't that olive oil scores *lower* — it's that Nutri-Score treats natural and industrial oils the same, ignoring processing level entirely. Look for outliers: coconut oils (often grade D/E, NOVA 2) and flavoured oil sprays (grade B, NOVA 4).

---

## Sharpen your angle

Before running the agent, consider editing this file to add:
- A specific country you want to focus on
- A specific product you already know is egregious (e.g., a coconut oil you recognise)
- Your headline hypothesis: "I think the oil category shows the clearest paradox"

The agent will pick up any context you add above.

---

## What comes next

Part 1 gives you a solid, presentable finding. When you're ready to go deeper,
continue with **Part 2** (`assignment-part-2.md`) — it adds NOVA processing data
to reveal the sharpest paradoxes: natural foods scoring badly, ultra-processed foods scoring well.

---

*Data: Open Food Facts (ODbL) — include attribution in your output.*
*Skill: `skills/openfoodfacts/SKILL.md` · Methods: `nutriscore_distribution()`, `nova_distribution()`, custom SQL*


# Assignment A — The Mediterranean Trap · Part 2: The NOVA Paradox

> This is the second part of the Mediterranean Trap investigation.
> **Part 1** (`assignment-part-1.md`) built an HTML page comparing Nutri-Score distributions
> for natural foods vs. industrial counterparts — olive oils vs. vegetable blends,
> nuts vs. chips, hard cheese vs. processed slices. You should have a working HTML output
> with bar charts and a headline finding before starting here.

---

## What Part 1 established

- Nutri-Score grades for olive oils, nuts, and hard cheeses vs. their industrial counterparts
- A bar chart showing the full A–E grade breakdown for each category
- A headline finding about how Nutri-Score treats natural and industrial foods similarly

Now you'll layer in **NOVA processing level** to find the sharpest paradoxes:
foods that are natural (NOVA 1–2) but score badly, and ultra-processed (NOVA 4) foods that score well.

---

## Part 2 — The NOVA paradox *(~15 min, harder)*

Tell your agent:

> *"Now add NOVA processing data to the comparison. Find products that are NOVA 1–2 (minimally processed) but score D or E — and any NOVA 4 (ultra-processed) products that score A or B. Add this to the HTML as a 'paradox products' section. Then do the same for nuts vs. chips-and-fries."*

**What to look for:**
- **Oils**: Coconut oil — NOVA 2, naturally saturated, scores D or E. Flavoured oil spray — NOVA 4, scores B. This is the clearest paradox in the oils category.
- **Nuts vs. chips**: `en:almonds` tends to score A/B (proteins, fibre rewarded). `en:chips-and-fries` tends to score C/D (fat, salt penalised). Here Nutri-Score actually aligns with nutrition science — nuts ARE better. The paradox is explaining *why* it doesn't work the same way for oils.
- **Cheese**: Hard cheeses and processed cheese slices score similarly (C/D) despite vastly different processing levels.

---

## Sharpen your angle

The goal is to find specific *named products* — not just category averages — that illustrate the paradox most sharply. Ask your agent:
- "What is the single most extreme example of a NOVA 2 product with a bad Nutri-Score?"
- "Find me a NOVA 4 product with an A or B grade and show me its ingredient list"

These specific cases make the best story leads.

---

*Data: Open Food Facts (ODbL) — include attribution in your output.*
*Skill: `skills/openfoodfacts/SKILL.md` · Methods: `nutriscore_distribution()`, `nova_distribution()`, custom SQL*
