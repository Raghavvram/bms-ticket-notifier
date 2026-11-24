  The custom tracker for Avengers: Doomsday on December 21, 2026 at PVR: VR Chennai is fully implemented, verified, and committed.
  ──────
  What Was Built & Implemented

  1. Flexible, Parameterized Configuration (main.py:21-75):
      • Configurable parameters with sensible defaults:
          • BMS_DATE="20261221"
          • BMS_THEATRE="VR Chennai" (fuzzy match handles "VR Mall", "PVR VR Mall")
          • BMS_LANGUAGE="English"
          • BMS_FORMAT="PXL,MS-Infinity Vision" (handles "PXL", "3D", "Infinity Vision", "Vsn")
          • BMS_LOCATION="chennai"
          • BMS_MOVIE="avengers-doomsday"
          • ALERT_BURST="3" (burst of 3 urgent emails to buzz your phone without hitting Resend limits)

  2. Resilient Matcher & Safe Fallbacks (main.py:320-400):
      • matches_theatre(): strips punctuation and filler words (mall, cinema, theatre), ensuring "VR Mall" matches BookMyShow's official
      "PVR: VR Chennai, Anna Nagar" while rejecting unrelated PVRs.
      • matches_format(): normalizes BookMyShow abbreviations (e.g. vsn → vision, 3-d → 3d).
      • If a custom filter doesn't match any chip, the script automatically falls back to monitoring all active formats for that movie
      rather than failing silently with 0 shows.
  3. Dynamic Format Discovery & Dual-Trigger Detection (main.py:240-280, L500-L545):
      • discover_format_event_codes(): dynamically queries format-selector chips from bottomSheetData so variant child event codes are
      never missed.
      • detect_dual_triggers(): watches both the date picker status (NOT_OPEN → BOOKABLE / AVAILABLE for Dec 21st) and new/restocked
      showtimes.
  4. Urgent Email Alert Flood with One-Click Booking (main.py:605-770):
      • As soon as Dec 21st tickets drop or the date opens, it sends ALERT_BURST (default 3) high-urgency emails with the subject:
      🚨 URGENT: AVENGERS: DOOMSDAY TICKETS OPEN - BOOK NOW!
      • Includes a large prominent "🎟️ BOOK TICKETS NOW" CTA button linking directly to BookMyShow's booking URL so you can jump straight
      to manual seat selection.
      • Also triggers desktop notifications (notify-send / macOS banners) when run locally.
  5. Anti-Rate-Limiting Protection (main.py:170-185):
      • Uses Chrome 145 User-Agent, sec-ch-ua client hints, and x-app-code: WEB.
      • Adds randomized request jitter delay (0.5s–1.5s) between BookMyShow calls to prevent edge rate limits.
  6. 5-Minute GitHub Actions Automation (.github/workflows/bms-checker.yml):
      • Scheduled to run every 5 minutes (*/5 * * * *) on GitHub's free tier.
      • Passes all environment variables with fallback defaults.
  7. Automated Test Suite (tests/):
      • Added 11 unit tests covering matcher aliases, format discovery fallbacks, dual-trigger date detection, alert templates, and email
      bursts. All 11 tests pass.

  ──────
  How to Run & Verify

  Run Locally

    # Execute the tracker (tracks Dec 21st at VR Chennai)
    uv run main.py

    # Run test suite
    uv run pytest

  GitHub Actions Setup (Free & Automated)

  Push your commits to your GitHub repository and add your Resend https://resend.com credentials in Settings → Secrets and variables →
  Actions → Secrets:

  • RESEND_API_KEY: Your Resend API key (e.g. re_...)
  • RESEND_TO_EMAIL: Your email address to receive notifications

  The workflow in .github/workflows/bms-checker.yml will run automatically every 5 minutes and flood your email the moment December 21st
  bookings open.
