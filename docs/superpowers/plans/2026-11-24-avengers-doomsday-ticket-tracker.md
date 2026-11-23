# Avengers Doomsday BMS Ticket Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build a parameterized, rate-limit-safe BookMyShow tracker that checks for tickets for *Avengers: Doomsday* on December 21, 2026 at PVR VR Chennai (English, PXL/MS-Infinity Vision) every 5 minutes via GitHub Actions, and sends an urgent flood of emails with direct booking links as soon as bookings open.

**Architecture:** A lightweight Python script that parses BookMyShow's dynamic API, auto-resolves format event codes from format-selector chips, applies fuzzy token matching for theatre/format/language inputs, detects both date openings and new showtimes, applies request jitter to prevent rate-limiting, and triggers high-urgency burst notifications.

**Tech Stack:** Python 3.14+, `requests`, `pytest` (for test suite), GitHub Actions cron.

**Spec:** [docs/superpowers/specs/2026-11-24-avengers-doomsday-ticket-tracker-design.md](file:///home/raghav/Public/temp/bms-ticket-notifier/docs/superpowers/specs/2026-11-24-avengers-doomsday-ticket-tracker-design.md)

## Global Constraints
- Location default: `chennai` (`CHEN`)
- Movie default: `avengers-doomsday`
- Date default: `20261221`
- Theatre default: `VR Chennai`
- Language default: `English`
- Format default: `PXL,MS-Infinity Vision`
- Alert burst count default: `3`
- GitHub Actions cron interval: `*/5 * * * *`
- State persistence: `bms_state.json` committed on change

## Review Focus
1. User provides alias `"VR Mall"` or `"PVR VR Mall"` which does not match official BMS string `"PVR: VR Chennai, Anna Nagar"` literally → token matching must resolve correctly without matching unrelated PVRs.
2. User provides format filter that does not match BMS's internal naming → safe fallback must check all formats rather than failing silently with 0 shows.
3. Date 20261221 is currently `NOT_OPEN` in date widget and BMS returns fallback shows for Dec 17 → date filter must drop fallback shows and accurately detect when the date status flips to `BOOKABLE`.
4. Ticket drop occurs → urgent burst must send exactly `ALERT_BURST` emails with direct BMS booking URLs, respecting Resend rate limits.
5. GitHub runner IP hitting BMS repeatedly → request headers, timeout handling, and random jitter (0.5s–1.5s) must prevent HTTP 429/403 blocks.

---

### Task 1: Resilient Input Parsing & Token-Based Matching

**Files:**
- Modify: `main.py`
- Create: `tests/test_matcher.py`

**Interfaces:**
- Consumes: Environment variables (`BMS_LOCATION`, `BMS_MOVIE`, `BMS_THEATRE`, `BMS_DATE`, `BMS_LANGUAGE`, `BMS_FORMAT`, `ALERT_BURST`, `BMS_TIME`)
- Produces:
  - `CONFIG: dict`
  - `matches_theatre(venue_name: str, filter_str: str) -> bool`
  - `matches_format(chip_title: str, screen_attr: str, format_filter: str) -> bool`
  - `matches_language(chip_lang: str, lang_filter: str) -> bool`

- [x] **Step 1: Write failing tests for matcher functions**
Create `tests/test_matcher.py` testing:
- `matches_theatre("PVR: VR Chennai, Anna Nagar", "VR Mall") == True`
- `matches_theatre("PVR: VR Chennai, Anna Nagar", "PVR VR Mall") == True`
- `matches_theatre("PVR: Sathyam, Royapettah", "VR Mall") == False`
- `matches_format("MS-Infinity Vsn 3d", "PXL", "PXL,MS-Infinity Vision") == True`
- `matches_format("2D", "", "PXL,MS-Infinity Vision") == False`
- `matches_language("English", "English") == True`
- `matches_language("Tamil", "English") == False`

- [x] **Step 2: Run test to verify it fails**
Run: `uv run pytest tests/test_matcher.py`
Expected: FAIL (missing `matches_format`, `matches_language`, or imports)

- [x] **Step 3: Implement matching and configuration in `main.py`**
Implement:
- `matches_theatre` with punctuation stripping and token intersection ignoring generic words.
- `matches_format` checking token intersection against chip titles and screen attributes.
- `matches_language` with case-insensitive prefix match.
- `CONFIG` schema reading all user-configurable parameters with sensible defaults.

- [x] **Step 4: Run test to verify it passes**
Run: `uv run pytest tests/test_matcher.py`
Expected: PASS (all tests pass)

- [x] **Step 5: Commit**
```bash
git add main.py tests/test_matcher.py
git commit -m "feat: add resilient matching for theatre, format, and language"
```

---

### Task 2: Multi-Format Dynamic Auto-Discovery & Dual-Trigger Date Detection

**Files:**
- Modify: `main.py`
- Create: `tests/test_discovery.py`

**Interfaces:**
- Consumes: BMS API response dict, `matches_format`, `matches_language`
- Produces:
  - `discover_format_event_codes(data: dict, target_lang: str, target_format: str) -> list[tuple[str, str, str]]`
  - `detect_dual_triggers(old_state: dict, new_state: dict, target_date: str) -> list[str]`

- [x] **Step 1: Write failing tests for format discovery and dual-trigger detection**
Create `tests/test_discovery.py` testing:
- Extracting format event codes from sample `bottomSheetData` widget structure.
- Fallback behavior: when no formats match the filter, return all discovered formats with a warning flag.
- Date status trigger: date `20261221` transitioning from `NOT_OPEN` to `BOOKABLE`.
- Show opening trigger: sold-out status `0` to available status `3` or new shows matching Dec 21.

- [x] **Step 2: Run test to verify it fails**
Run: `uv run pytest tests/test_discovery.py`
Expected: FAIL

- [x] **Step 3: Implement format discovery and dual-trigger detection in `main.py`**
Implement:
- `discover_format_event_codes(data, target_lang, target_format)` extracting `(event_code, language, format)`.
- If filtered list is empty, fallback to all format codes.
- `detect_dual_triggers(old_state, new_state, target_date)` prioritizing date booking opening and show openings.

- [x] **Step 4: Run test to verify it passes**
Run: `uv run pytest tests/test_discovery.py`
Expected: PASS

- [x] **Step 5: Commit**
```bash
git add main.py tests/test_discovery.py
git commit -m "feat: add dynamic format discovery and dual-trigger detection"
```

---

### Task 3: Rate Limiting Protection & High-Urgency Email Flood

**Files:**
- Modify: `main.py`
- Create: `tests/test_alert.py`

**Interfaces:**
- Consumes: `detect_dual_triggers()`, `CONFIG["alert_burst"]`, `CONFIG["url"]`
- Produces:
  - `apply_request_jitter(min_sec: float = 0.5, max_sec: float = 1.5)`
  - `send_urgent_alert(subject: str, changes: list[str], shows: list, movie_info: dict, booking_url: str, burst_count: int)`

- [x] **Step 1: Write failing tests for alert formatting and burst generation**
Create `tests/test_alert.py` testing:
- Email subject containing `🚨 URGENT:` and direct booking link embedded in HTML button and plain text.
- Burst logic verifies sending `burst_count` emails when urgent triggers fire.
- Rate-limiting headers validation.

- [x] **Step 2: Run test to verify it fails**
Run: `uv run pytest tests/test_alert.py`
Expected: FAIL

- [x] **Step 3: Implement jitter, alert template, and burst sending in `main.py`**
Implement:
- Request jitter before outbound requests.
- `send_urgent_alert()` with large "BOOK NOW" button linking directly to BookMyShow buytickets URL.
- Loop to send `burst_count` alerts on high-priority ticket openings.

- [x] **Step 4: Run test to verify it passes**
Run: `uv run pytest tests/test_alert.py`
Expected: PASS

- [x] **Step 5: Commit**
```bash
git add main.py tests/test_alert.py
git commit -m "feat: add rate-limiting protection and urgent email burst"
```

---

### Task 4: GitHub Actions Workflow Optimization, State Sync & Documentation

**Files:**
- Modify: `.github/workflows/bms-checker.yml`
- Modify: `README.md`

**Interfaces:**
- Consumes: All `BMS_*` and `ALERT_BURST` environment variables
- Produces: 5-minute GitHub Actions automation and updated documentation

- [x] **Step 1: Update `.github/workflows/bms-checker.yml`**
- Set cron schedule to `*/5 * * * *`.
- Expose all configurable environment variables with default values:
  - `BMS_LOCATION: ${{ vars.BMS_LOCATION || 'chennai' }}`
  - `BMS_MOVIE: ${{ vars.BMS_MOVIE || 'avengers-doomsday' }}`
  - `BMS_THEATRE: ${{ vars.BMS_THEATRE || 'VR Chennai' }}`
  - `BMS_DATE: ${{ vars.BMS_DATE || '20261221' }}`
  - `BMS_LANGUAGE: ${{ vars.BMS_LANGUAGE || 'English' }}`
  - `BMS_FORMAT: ${{ vars.BMS_FORMAT || 'PXL,MS-Infinity Vision' }}`
  - `ALERT_BURST: ${{ vars.ALERT_BURST || '3' }}`

- [x] **Step 2: Update `README.md`**
- Document setup for GitHub Actions Secrets (`RESEND_API_KEY`, `RESEND_TO_EMAIL`).
- Document all configurable GitHub Variables.
- Document local execution and test commands.

- [x] **Step 3: End-to-End Verification**
Run:
```bash
uv run pytest
uv run main.py --dry-run
```
Expected: All tests pass, live BookMyShow query for Dec 21 executes cleanly, reports discovered formats and date status (`NOT_OPEN`), and exits with code 0.

- [x] **Step 4: Commit**
```bash
git add .github/workflows/bms-checker.yml README.md
git commit -m "chore: configure 5-minute cron schedule and update documentation"
```
