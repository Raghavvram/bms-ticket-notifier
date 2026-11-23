# BMS Ticket Notifier — Avengers Doomsday Tracker

Automatically monitors [BookMyShow](https://in.bookmyshow.com) for ticket availability and sends an urgent flood of emails and desktop alerts the instant ticket bookings open.

Configured by default to track **Avengers: Doomsday** for **December 21, 2026** at **PVR: VR Chennai, Anna Nagar** (English, PXL / MS-Infinity Vision).

Runs automatically every **5 minutes** for free via **GitHub Actions** cron.

---

## Features

- **Dual-Trigger Detection:**
  - Monitors the BookMyShow date picker status (`NOT_OPEN` → `BOOKABLE` / `AVAILABLE` on Dec 21st).
  - Monitors showtime listings and seat statuses (`SOLD OUT` → `AVAILABLE` / `FILLING FAST`).
- **Dynamic Format Auto-Discovery:**
  - Automatically queries BookMyShow's format-selector chips (e.g. `ET00526306` for MS-Infinity Vision 3D) so tickets aren't missed if published under variant child event codes.
- **Resilient & Fuzzy Input Matching:**
  - Tolerates theatre aliases (e.g. `VR Mall` or `PVR VR Mall` automatically matches `PVR: VR Chennai, Anna Nagar`).
  - Normalizes abbreviations (e.g. `Vision` matches `Vsn`).
  - Safe fallback: if a custom format filter matches no chips, automatically falls back to checking all formats instead of failing silently.
- **Urgent Notification Flood:**
  - Sends a configurable burst of high-urgency emails (default: 3 emails) with direct one-click **"BOOK TICKETS NOW"** links.
  - Triggers local desktop notifications (`notify-send` on Linux / macOS banners) when run locally.
- **Rate-Limiting Protection:**
  - Employs realistic browser headers (`User-Agent`, `sec-ch-ua`, `x-app-code: WEB`).
  - Applies randomized request jitter (0.5s–1.5s) and backoff handling to prevent IP bans.

---

## Setup for GitHub Actions

### 1. Fork or push this repository to GitHub

### 2. Set GitHub Secrets (For Email Alerts)

Go to **Settings → Secrets and variables → Actions → Secrets** and add:

| Secret | Description | Example |
|--------|-------------|---------|
| `RESEND_API_KEY` | API key from [resend.com](https://resend.com) | `re_123456789...` |
| `RESEND_TO_EMAIL` | Email address where you want to receive alerts | `you@gmail.com` |
| `RESEND_FROM_EMAIL` | Sender address (optional, defaults to `onboarding@resend.dev`) | `onboarding@resend.dev` |

### 3. Set GitHub Variables (Optional — Defaults are already set for Dec 21 at VR Chennai)

Go to **Settings → Secrets and variables → Actions → Variables** to override any parameters:

| Variable | Description | Default |
|----------|-------------|---------|
| `BMS_DATE` | Target date (YYYYMMDD) | `20261221` |
| `BMS_THEATRE` | Theatre name or alias | `VR Chennai` |
| `BMS_LANGUAGE` | Preferred language | `English` |
| `BMS_FORMAT` | Preferred screen format | `PXL,MS-Infinity Vision` |
| `BMS_LOCATION` | City name / region | `chennai` |
| `BMS_MOVIE` | BMS movie slug | `avengers-doomsday` |
| `ALERT_BURST` | Number of alert emails sent in rapid succession | `3` |
| `BMS_TIME` | Optional time filter (`morning`, `afternoon`, `evening`, `night`) | *(all shows)* |

### 4. Enable the Workflow

Go to the **Actions** tab in your repository and ensure workflows are enabled. The checker runs automatically every 5 minutes. You can also click **Run workflow** anytime for a manual test.

---

## Local Usage

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```bash
# 1. Install dependencies
uv sync

# 2. Run the tracker
uv run main.py

# 3. Run the tracker with immediate status alert (dry-run / test notification)
uv run main.py --notify-current

# 4. Run the automated test suite
uv run pytest
```
