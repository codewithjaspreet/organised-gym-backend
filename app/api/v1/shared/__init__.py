from fastapi import APIRouter
from .auth import router as auth_router
from .gyms import router as gyms_router
from .plans import router as plans_router
from .memberships import router as memberships_router
from .billing import router as billing_router
from .attendance import router as attendance_router
from .announcements import router as announcements_router
from .bank_accounts import router as bank_accounts_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(bank_accounts_router)
# router.include_router(gyms_router)
# router.include_router(plans_router)
# router.include_router(memberships_router)
# router.include_router(billing_router)
# router.include_router(attendance_router)
# router.include_router(announcements_router)

