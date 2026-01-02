from fastapi import APIRouter

router = APIRouter(prefix="/announcements", tags=["announcements"])

# General announcements endpoints (if needed beyond role-specific ones)
# Role-specific announcements are handled in roles/owners/

