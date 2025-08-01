# 🗓️ Joplin Planner

Generate Markdown-based planners for [Joplin](https://joplinapp.org/) to help you track habits, set goals, and plan your month or week. This tool outputs clean, checkbox-friendly tables ready to paste directly into your notes.

---

## 📦 Installation (with [uv](https://github.com/astral-sh/uv))

1. Install [uv](https://github.com/astral-sh/uv):
   ```bash
   pipx install uv
   ```

1. Install all runtime dependencies::
   ```bash
   uv sync --frozen
   ```

1. Run the simulation:
   ```bash
   uv run main.py
   ```

---

## 🛠 Development Setup
To install all dependencies including development extras and pre-commit hooks:

Install all dependencies:
   ```bash
   uv sync --all-extras --frozen
   pre-commit install
   ```

------

## 🚀 Usage

### 📅 Monthly Planner
Generate a markdown file for the **current** or **next** month with up to **5 habit columns**:

```bash
joplin-planner monthly \
  --habits "Workout" "Read" "Sleep Early" \
  --month current \
  --output planner.md
```

#### Options:
- `--habits` / `-h`: Up to 5 habit names
- `--month` / `-m`: Either `current` (default) or `next`
- `--output` / `-o`: File to save the generated markdown

---

## 🛠 Development

This project uses:
- [`ruff`](https://docs.astral.sh/ruff/): fast Python linter
- [`mypy`](http://mypy-lang.org/): optional static typing
- [`pre-commit`](https://pre-commit.com/): automatic formatting and checks

### Run manually
```bash
python main.py monthly --habits "Hydrate" "Meditate" --month next
```

### Run tests (if applicable)
```bash
pytest
```

---

## 🔮 Roadmap
- [x] Monthly planner with habits
- [ ] Weekly planner with daily blocks
- [ ] Daily page generator (journaling style)
- [ ] GUI or web interface

---

## 📄 License
GPL-3.0

---

## 💡 Example Output (Snippet)
```markdown
| Day | Weekday | Highlight | Workout | Read | Sleep Early |
|-----|---------|-----------|---------|------|--------------|
| 01  | Thu     |           | [ ]     | [ ]  | [ ]          |
| 02  | Fri     |           | [ ]     | [ ]  | [ ]          |
...
```

Ready to paste into your Joplin note!
