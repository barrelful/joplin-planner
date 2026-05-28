# 🗓️ Joplin Planner

Generate Markdown-based planners for [Joplin](https://joplinapp.org/) to help you track habits, set goals, and plan your month, week, or day. This tool outputs clean, checkbox-friendly tables ready to paste directly into your notes.

---

## 📦 Installation (with [uv](https://github.com/astral-sh/uv))

1. Install [uv](https://github.com/astral-sh/uv):
   ```bash
   pipx install uv
   ```

2. Install all runtime dependencies:
   ```bash
   uv sync --frozen
   ```

3. Run the planner:
   ```bash
   uv run main.py monthly --habits "Workout" "Read"
   ```

---

## 🛠 Development Setup

To install all dependencies including development extras and pre-commit hooks:

```bash
uv sync --all-extras --frozen
pre-commit install
```

---

## 🚀 Usage

The CLI provides three subcommands: `monthly`, `weekly`, and `daily`. All output is printed to **stdout** — redirect to a file with `>` if needed.

### 📅 Monthly Planner

Generate a markdown table for the **current** or **next** month with up to **5 habit columns**:

```bash
joplin-planner monthly --habits "Workout" "Read" "Sleep Early" > planner.md
```

Or run without habits for a simple day-by-day outline:

```bash
joplin-planner monthly
```

#### Options:
- `--habits`: List of habit names to track (max 5)
- `--next`: Generate for the **next** month instead of the current one

---

### 🗓️ Weekly Planner

Generate a weekly planner with time blocks for each day:

```bash
joplin-planner weekly --start 8 --end 22 --interval 2 --format 24h > week.md
```

#### Options:
- `--start`: Start hour of the day (0–23), default `8`
- `--end`: End hour of the day (1–24), default `22`
- `--interval`: Time-block interval — `1` for hourly or `2` for every 2 hours (default `2`)
- `--format`: Hour format — `12h` or `24h` (default `24h`)
- `--next`: Generate for the **next** week instead of the current one

---

### 📋 Daily Planner

Generate a structured daily planner with optional holiday and fun-date detection:

```bash
joplin-planner daily --date 2026-06-02 > daily.md
```

Or generate for today or tomorrow:

```bash
joplin-planner daily --today
joplin-planner daily --tomorrow
```

#### Options:
- `--date`: Specific date (YYYY-MM-DD)
- `--today`: Generate for today
- `--tomorrow`: Generate for tomorrow
- `--fun-dates`: Path to custom fun dates JSON
- `--holiday-region`: Region for holidays (default: england-and-wales)
- `--no-holidays`: Skip holiday detection
- `--no-fun-dates`: Skip fun dates

#### Holidays

Holidays are detected from a local cached copy of GOV.UK bank holidays for England and Wales. No internet is required. If holiday data is unavailable, the planner generates without the holiday section and prints a warning.

#### Fun Dates

Fun and commemorative dates come from a local curated JSON file (`src/data/fun_dates.json`). Each entry uses an MM-DD key (e.g., `03-14` for Pi Day) so dates repeat yearly. To add a new fun date, edit `src/data/fun_dates.json` and add an entry like: `{"name": "...", "note": "..."}`

---

## 🛠 Development

This project uses:
- [`ruff`](https://docs.astral.sh/ruff/): fast Python linter and formatter
- [`mypy`](http://mypy-lang.org/): optional static typing
- [`pre-commit`](https://pre-commit.com/): automatic formatting and checks

### Run manually
```bash
python main.py monthly --habits "Hydrate" "Meditate" --next
python main.py weekly --start 9 --end 18 --interval 1 --format 12h
```

---

## 🔮 Roadmap
- [x] Monthly planner with habits
- [x] Weekly planner with daily blocks
- [x] Daily page generator (journaling style)
- [ ] GUI or web interface

---

## 📄 License
GPL-3.0

---

## 💡 Example Output

### Monthly Snippet
```markdown
# Monthly Planner – August 2025

## Main Goals of the Month

- [ ] Goal 1
- [ ] Goal 2
- [ ] Goal 3

## Day Highlights

| Day | Weekday | Highlight | Workout | Read | Sleep Early |
|-----|---------|-----------|---------|------|-------------|
| 01  | Fri     |           | [ ]     | [ ]  | [ ]         |
| 02  | Sat     |           | [ ]     | [ ]  | [ ]         |
...
```

### Weekly Snippet
```markdown
# 🗓️ Weekly Planner – 11 to 17th of May 2026

## Overview and main objective

Week brief summary and goal

- [ ] Objective 1
- [ ] Objective 2

## Weekly planner

|     | 11/05 | 12/05 | 13/05 | 14/05 | 15/05 | 16/05 | 17/05 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| --- | Monday | Tuesday | Wednesday | Thursday | Friday | Saturday | Sunday |
| 08:00 to 10:00 |  |  |  |  |  |  |  |
| 10:00 to 12:00 |  |  |  |  |  |  |  |
| 12:00 to 14:00 |  |  |  |  |  |  |  |
...
```

### Daily Snippet
```markdown
# Daily Plan - 2026-03-14

> Saturday, 14 March 2026
> Fun dates: Pi Day — Celebrating the mathematical constant π (3.14159...); Pie Day — Enjoy your favorite pie today!
> Mercury note: Do the next right thing.

## Main objective
*

## Top priorities
* [ ]
* [ ]
* [ ]

## Schedule / constraints
*

## Must do
* [ ]

## Should do
* [ ]

## Nice to do
* [ ]

## Health / maintenance
* [ ]

## Carryover
* [ ]

## Notes
*

## Evening close-out
* Done:
* Still open:
* First action tomorrow:
```

Ready to paste into your Joplin note!
