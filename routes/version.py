from fastapi import APIRouter
from config.config import MIN_SUPPORTED_VERSION, LATEST_VERSION, FORCE_UPDATE_MESSAGE

router = APIRouter()

@router.get("/app/version")
def get_version_info():
	return {
		"latest_version": LATEST_VERSION,
		"min_supported_version": MIN_SUPPORTED_VERSION,
		"force_update_message": FORCE_UPDATE_MESSAGE,
	}