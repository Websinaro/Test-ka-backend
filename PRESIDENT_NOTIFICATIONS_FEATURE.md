# President Dashboard + Notification Center

## Backend (this repo)

### Signup as President
- `POST /register` now accepts an optional `access_code`.
- If `access_code` matches `PRESIDENT_ACCESS_CODE` (env var, defaults to
  `KDMA-PRESIDENT-2026` for local dev - **set a real one in production**),
  the account is created with `role="president"`.
- If `access_code` is provided but wrong, registration is rejected
  (400 Invalid president access code).
- Omit `access_code` entirely to sign up as a normal citizen, same as before.

### President Dashboard
- `GET /president/dashboard` (president only) returns:
  - `total_users`, `total_active_sos`, `total_active_notifications`
  - `districts[]`: per-district registered users, active SOS count, active
    notification count
  - `active_sos_alerts[]`: every currently-active SOS statewide, with
    sender name, district, coordinates, message, timestamp

### Notification Center (CRUD)
- `POST /notifications` (president only) - create + broadcast-push an alert
  to a specific district or all Kerala (`district: null`).
- `GET /notifications` - president sees everything they've sent; everyone
  else sees active alerts for their district + statewide alerts.
- `GET /notifications/{id}`
- `PUT /notifications/{id}` (president, own alerts only) - edit
  title/message/severity/target, or toggle `active` to deactivate /
  reactivate (reactivating re-sends the push).
- `DELETE /notifications/{id}` (president, own alerts only)

### New/changed files
- `model/model.py` - `Notification` model
- `scheme/notification_scheme.py`, `scheme/president_scheme.py`
- `routes/notifications.py`, `routes/president.py`
- `security/oauth2.py` - `require_president` dependency
- `services/push_service.py` - `send_admin_alert_push`
- `config/config.py` - `PRESIDENT_ACCESS_CODE`
- `scheme/scheme.py` - `UserCreate.access_code`
- `routes/auth.py` - role assignment on register
- `alembic/versions/0002_notifications_table.py`
- `main.py` - routers wired in

### Env var to set in production
```
PRESIDENT_ACCESS_CODE=<a real secret you distribute to actual coordinators>
```
