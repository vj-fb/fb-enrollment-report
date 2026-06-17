# Enrollment & CRM Funnel Analysis

Interactive, self-contained HTML report built from `CRMDetailsByCreatedDate (1).csv`
(7,020 records, 9 schools, Jun 2024 → Jun 2026). All data is embedded in `index.html`,
so every filter works with **no server** — just open the file or host it as a static page.

## Files
- `index.html` — the report (open in any browser, or deploy as-is).
- `generate.py` — rebuilds `index.html` from the source CSV. Run `python3 generate.py`
  after updating the CSV path at the top of the script.
- `server.py` — tiny local static server for previewing (`python3 server.py` → http://127.0.0.1:8753).

## Filters
- **School** — All or any of the 9 centers.
- **Date range** — Today, Yesterday, Current month, Previous month, Last 3 months,
  Last 6 months, This year (YTD), Last year, All time, or a Custom from/to range.
  "Today"-style presets are relative to the viewer's current date.

## Deploy to GitHub Pages
```sh
cd enrollment-report
git init
git add index.html            # README/generate.py optional
git commit -m "Enrollment CRM analysis report"
gh repo create fb-enrollment-report --public --source=. --push
# then in the repo: Settings → Pages → Branch: main / root → Save
```
Your report will be live at `https://<user>.github.io/fb-enrollment-report/`.

## Refreshing the data later
Replace the CSV, run `python3 generate.py`, commit the new `index.html`, and push.
