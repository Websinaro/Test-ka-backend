from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import get_db
from data.kerala_districts import KERALA_DISTRICTS
from model import model
from scheme import president_scheme
from security.oauth2 import require_president

router = APIRouter()


@router.get("/president/dashboard", response_model=president_scheme.PresidentDashboard)
def get_president_dashboard(
	db: Session = Depends(get_db),
	current_user: model.User = Depends(require_president),
):
	"""District-wise rollup for the president's command dashboard: how many
	registered citizens, how many currently-active SOS emergencies, and how
	many alerts the president currently has live, per district - plus the
	raw list of active SOS alerts (with sender name + district) so they can
	be plotted or triaged directly from the dashboard."""

	all_users = db.query(model.User).all()
	users_by_id = {u.id: u for u in all_users}

	active_sos = db.query(model.SosAlert).filter(model.SosAlert.status == "active").all()
	active_notifications = db.query(model.Notification).filter(
		model.Notification.active == True,  # noqa: E712
		model.Notification.created_by == current_user.id,
	).all()

	district_users: dict[str, int] = {d: 0 for d in KERALA_DISTRICTS}
	for u in all_users:
		if u.district in district_users:
			district_users[u.district] += 1

	district_sos: dict[str, int] = {d: 0 for d in KERALA_DISTRICTS}
	sos_summaries = []
	for alert in active_sos:
		sender = users_by_id.get(alert.user_id)
		district = sender.district if sender else None
		if district in district_sos:
			district_sos[district] += 1
		sos_summaries.append(
			president_scheme.ActiveSosSummary(
				id=alert.id,
				user_id=alert.user_id,
				user_name=sender.name if sender else "Unknown",
				district=district or "unknown",
				latitude=alert.latitude,
				longitude=alert.longitude,
				message=alert.message,
				created_time=alert.created_time,
			)
		)

	district_notifications: dict[str, int] = {d: 0 for d in KERALA_DISTRICTS}
	for n in active_notifications:
		if n.district is None:
			# All-Kerala alert counts against every district.
			for d in district_notifications:
				district_notifications[d] += 1
		elif n.district in district_notifications:
			district_notifications[n.district] += 1

	districts = [
		president_scheme.DistrictStat(
			district=d,
			registered_users=district_users[d],
			active_sos=district_sos[d],
			active_notifications=district_notifications[d],
		)
		for d in KERALA_DISTRICTS
	]

	return president_scheme.PresidentDashboard(
		total_users=len(all_users),
		total_active_sos=len(active_sos),
		total_active_notifications=len(active_notifications),
		districts=districts,
		active_sos_alerts=sos_summaries,
	)
