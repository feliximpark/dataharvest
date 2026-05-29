# AGENTS.md

You are in a workshop VM provisioned by `dev-orchestrator`.

## Public URLs

- Live app: https://dh-46.dataharvest.casus.org/ proxies to localhost:3000
- Static reports: https://dh-46.dataharvest.casus.org/output/<file>.html serves ~/output/<file>.html
- Status: https://dh-46.dataharvest.casus.org/status and /status.json

Do not install tunneling tools. Caddy already exposes the VM with TLS.
To expose a dev server, bind it to 3000 and verify with:

    curl -sf --max-time 5 http://localhost:3000/ > /dev/null

Static HTML reports should be written to `~/output`.

## Environment

- Workspace: ~/workshop (assignments, skills, data, output).
- Boilerplate: ~/dev/workshop-boilerplate (ops-managed source).
- Env: BASE_DOMAIN=dataharvest.casus.org, DEV_PORT=3000, sourced from ~/.config/dev/env.sh.
- Tools: pi, claude, node/npm, gh, rg, fd, jq, tmux, git, curl.
- Shells auto-attach to tmux; do not manage tmux unless asked.

## OpenFoodFacts

Read assignment + skills/openfoodfacts/SKILL.md first. Use ~/workshop;
data is ~/data/openfoodfacts. Do not search / or
download data. Validate categories with counts, missing Nutri/NOVA rates,
samples, and n.
Visuals for lay readers: prefer sorted bars/dot plots; avoid academic
charts (especially radar) and overlapping legend text. Use takeaway titles.

