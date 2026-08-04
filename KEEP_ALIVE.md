# Why the app "feels slow to open" — read this first

Before anything else: the single biggest speed problem in this project is not
in the code. It's in the hosting tier.

`lib/services/api_service.dart` in the frontend has this comment, written by
whoever built it:

> Base URL points at the Render deployment. Render's free tier spins the
> service down when idle, so the first request after a while can take
> 20-50s to "wake up".

That's confirmed by the 50-second timeout that was set on every API call to
compensate for it. **For an emergency SOS app, a backend that can take up to
50 seconds to respond to a help request is not production-grade, no matter
how fast the code is.** All the query/indexing/middleware fixes in this
package make every *warm* request meaningfully faster, but they cannot make a
sleeping server answer instantly — only two things can:

## Fix it properly (recommended)

Move off the free/sleeping tier to an always-on plan:
- Render: the paid "Starter" instance type or above does not sleep.
- Alternatives that don't sleep on entry-level paid plans: Railway, Fly.io,
  a small DigitalOcean/Hetzner VM, or AWS/GCP always-on containers.

This is the only real fix. Everything below is a mitigation, not a cure.

## Mitigate it if you must stay on a free tier

Point an external uptime pinger at the new `/health` endpoint every 5–10
minutes so the service rarely goes to sleep in the first place:
- UptimeRobot (free tier supports this)
- cron-job.org (free)
- A scheduled GitHub Action hitting `curl https://<your-app>/health`

This reduces how often a real user hits a cold start, but during genuinely
idle windows (overnight, low traffic) the server can still sleep and the
next request will still be slow. It is not a substitute for an always-on
plan for a disaster-response app.

## What was changed in the app to cope gracefully either way

- `_send()` in `api_service.dart` now fails fast (8s) on the first attempt
  and retries once with a longer timeout, surfacing a clear "waking up the
  server, retrying…" state to the UI instead of a silent 50-second spinner.
- The splash screen no longer blocks navigation on network calls it doesn't
  need to.
- SOS sends immediately using the last known device location instead of
  waiting on a fresh GPS fix, so the *client-side* portion of "time to SOS
  sent" is minimized regardless of server speed.
