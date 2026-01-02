from fastapi import APIRouter

router = APIRouter(prefix="/notifications", tags=["notifications"])

# General notifications endpoints (if needed beyond role-specific ones)
# Role-specific notifications are handled in roles/owners/

