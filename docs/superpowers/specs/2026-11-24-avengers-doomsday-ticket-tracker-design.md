# Design Document: Avengers Doomsday BMS Ticket Tracker

**Date:** 2026-11-24  
**Topic:** Parameterized BookMyShow Ticket Tracker with Urgent Alerting  

---

## 1. Intent and Why
The user missed advance bookings for the opening week (Dec 17–20, 2026) of *Avengers: Doomsday* in Chennai, which are already sold out.
The goal is to monitor BookMyShow specifically for **December 21, 2026** at **PVR: VR Chennai, Anna Nagar** (English, PXL / MS-Infinity Vision, across morning, afternoon, or evening shows).
As soon as booking opens for December 21st, the tool must send an urgent burst of emails with direct booking links urging the user to book immediately, while running automatically on GitHub Actions cron for free without getting rate-limited by BookMyShow.

---

## 2. Goals, Non-Goals, Anti-Goals

### Goals
- **Parameterized configuration:** Support configuring target location (`chennai`), movie (`avengers-doomsday`), theatre (`VR Chennai` / `VR Mall`), date (`20261221`), language (`English`), and format (`PXL, MS-Infinity Vision`).
- **Multi-Format Auto-Discovery:** Query the movie listing and automatically discover all matching format event codes (e.g. `ET00526306` for MS-Infinity Vision 3D), so tickets aren't missed if published under variant event codes.
- **Dual-Trigger Detection:** Monitor both:
  1. Date status transitions (`NOT_OPEN` → `BOOKABLE` / `AVAILABLE` for `20261221`).
  2. Actual showtimes appearing for Dec 21 at PVR VR Chennai with seat availability > 0 (or new shows added).
- **Urgent Notification ("Flood") Mode:**
  - High-urgency email subject line: `🚨 URGENT: AVENGERS DOOMSDAY DEC 21 TICKETS OPEN AT PVR VR CHENNAI - BOOK NOW!`
  - Prominent one-click booking buttons/links in HTML and plain text directly to the BMS booking page.
  - Urgent burst: Send a configurable burst of emails (default: 3 emails) on ticket drop to persistently notify the user's phone, while respecting Resend's daily free quota limits (100/day).
  - Also trigger local desktop notifications (`notify-send` / macOS notification) when executed locally.
- **Rate-limit & Anti-block Protection:**
  - Realistic browser request headers (`User-Agent`, `sec-ch-ua`, `x-app-code: WEB`, `Referer`).
  - Randomized request jitter delay between queries.
  - Safe error handling with exponential backoff on HTTP 429/403.
- **GitHub Actions Cron Automation:**
  - Run every 5 minutes (`*/5 * * * *`) via GitHub Actions free tier.
  - Persist run state in `bms_state.json` via git commit on changes.

### Non-Goals
- Automated ticket purchase / CAPTCHA solving (booking is done manually by the user via the direct link).
- Supporting non-BookMyShow platforms (Paytm, etc.) in this iteration.

### Anti-Goals
- Do not make aggressive parallel requests that trigger BookMyShow Cloudflare / Akamai IP ban on GitHub runner IPs.
- Do not exceed Resend's free tier limits (avoid infinite email loops).

---

## 3. Constraints
- **BookMyShow API Structure:**
  - Format-specific event codes (e.g., base `ET00439706` vs format `ET00526306`).
  - Dates not yet open return `styleId: date-disabled` (`NOT_OPEN`) in `topStickyWidgets`.
  - Theatres are identified by official venue names (e.g. `PVR: VR Chennai, Anna Nagar`).
- **GitHub Actions Cron:** Minimum cron interval supported is 5 minutes (`*/5 * * * *`). GitHub runner scheduling may have small jitter.
- **Resend Free Tier:** 100 emails/day, 3,000 emails/month.

---

## 4. Approaches Considered

### Approach 1: High-Level Parameterized Tracker with Multi-Format Auto-Discovery (Selected)
- Resolves movie slug and format chips dynamically.
- Automatically handles format and event code changes.
- Flexible matching for theatre aliases (`VR Mall` -> `PVR: VR Chennai, Anna Nagar`).
- **Why selected:** It is resilient to BMS releasing Dec 21 shows under new event codes or format variants, and provides the exact user-facing parameter inputs requested.

### Approach 2: Fixed Event-Code Direct Poller
- Directly polls only `ET00526306` with hardcoded URL.
- **Trade-off:** High risk of missing tickets if BMS publishes Dec 21 tickets under a different format code or new event ID. Rejected.

---

## 5. Architectural Specification

### 5.1 Configuration Schema (`CONFIG`)
```python
CONFIG = {
    "location": os.getenv("BMS_LOCATION", "chennai"),
    "movie": os.getenv("BMS_MOVIE", "avengers-doomsday"),
    "theatre": os.getenv("BMS_THEATRE", "VR Chennai"),
    "date": os.getenv("BMS_DATE", "20261221"),
    "language": os.getenv("BMS_LANGUAGE", "English"),
    "format": os.getenv("BMS_FORMAT", "PXL,MS-Infinity Vision"),
    "time_period": os.getenv("BMS_TIME", ""),
    "alert_burst": int(os.getenv("ALERT_BURST", "3")),
    "url": os.getenv("BMS_URL", ""),
}
```

### 5.2 Resilient Matching, Fuzzy Resolution, and Safe Fallbacks
To handle discrepancies between user input and BookMyShow's internal strings:
1. **Theatre Resolution (Fuzzy / Token Matching):**
   - Strips punctuation and generic filler words (`mall`, `cinema`, `cinemas`, `theatre`, `theater`, `multiplex`).
   - Matches core tokens (e.g., input `"VR Mall"` or `"PVR VR Mall"` matches BMS venue `"PVR: VR Chennai, Anna Nagar"` because core tokens `pvr` and `vr` intersect).
   - If no venue matches the filter, the tracker logs all discovered venue names in that region to aid troubleshooting rather than silently failing.
2. **Format & Language Resolution:**
   - Format matching inspects both `bottomSheetData` chip titles (`MS - Infinity Vision`, `MS-Infinity Vsn 3d`) and show screen attributes (`PXL`).
   - Token-based matching (e.g. `"infinity"`, `"pxl"`, `"3d"`).
   - **Safe Fallback:** If the specified format does not match any known chip, the tracker falls back to monitoring **all active formats** for that movie and logs the available formats, ensuring no tickets are missed due to a naming mismatch.
3. **Movie & URL Resolution:**
   - Accepts either a high-level slug (`avengers-doomsday`), movie name (`Avengers: Doomsday`), or direct BookMyShow URL (which always has precedence).
   - Automatically resolves region codes, coordinates, and geohashes from the location string (`chennai` -> `CHEN`).

### 5.3 Detection & Alerting
- If date `20261221` transitions from `NOT_OPEN` to `BOOKABLE`/`AVAILABLE`: **Trigger Urgent Alert**.
- If new show matching PVR VR Chennai appears on `20261221` with available seats: **Trigger Urgent Alert**.
- If previously sold-out seats become available: **Trigger Alert**.
- **Urgent Alert Action:**
  - Send `ALERT_BURST` (default 3) emails in rapid succession via Resend with direct booking link.
  - Log high-priority console alert.
  - Send local desktop notification if run locally.

### 5.4 Anti-Rate-Limit Measures
- Realistic Chrome 145 User-Agent & Client Hints.
- 0.5s–1.5s randomized jitter between API calls.
- Timeout handling and backoff on HTTP 429/503.

---

## 6. What's Left to the Builder
- Implementing the parameterized configuration and format matching in `main.py`.
- Creating the high-urgency email template with direct booking CTA.
- Updating `.github/workflows/bms-checker.yml` to run every 5 minutes (`*/5 * * * *`).
- Updating documentation in `README.md`.
- Verifying the implementation against live BookMyShow responses.
