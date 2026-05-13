# 🗓️ Joplin Planner

Generate Markdown-based planners for [Joplin](https://joplinapp.org/) to help you track habits, set goals, and plan your month or week. This tool outputs clean, checkbox-friendly tables ready to paste directly into your notes.

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

The CLI provides two subcommands: `monthly` and `weekly`. All output is printed to **stdout** — redirect to a file with `>` if needed.

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
- [ ] Daily page generator (journaling style)
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

Ready to paste into your Joplin note!
