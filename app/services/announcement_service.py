import logging
from typing import List
from datetime import datetime
from sqlmodel import select
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.announcement import Announcement, SendToType
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementResponse,
    AnnouncementUpdate,
    PlatformAnnouncementCreate,
)
from app.models.user import User

# Setup logger
logger = logging.getLogger(__name__)


class AnnouncementService:

    def __init__(self, session: SessionDep):
        self.session = session

    def create_announcement(self, announcement: AnnouncementCreate) -> AnnouncementResponse:
        """Create a new announcement and send FCM notifications to gym members based on send_to filter"""
        from app.utils.fcm_notification import send_fcm_notification_to_gym_members_by_filter
        from app.core.exceptions import ValidationError
        
        # Validate member_ids when send_to is "Specific Members"
        if announcement.send_to.value == SendToType.SPECIFIC_MEMBERS:
            if not announcement.member_ids or len(announcement.member_ids) == 0:
                raise ValidationError(detail="member_ids is required when send_to is 'Specific Members'")
        
        db_announcement = Announcement(
            gym_id=announcement.gym_id,
            user_id=announcement.user_id,
            title=announcement.title,
            message=announcement.message,
            is_active=announcement.is_active,
            send_to=announcement.send_to,
            member_ids=announcement.member_ids
        )
        self.session.add(db_announcement)
        self.session.commit()
        self.session.refresh(db_announcement)
        
        if announcement.is_active:
            try:
                notification_data = {
                    "announcement_id": db_announcement.id,
                    "type": "announcement",
                    "gym_id": announcement.gym_id
                }
                route = "/gym-details" 
                if announcement.data and announcement.data.route:
                    route = announcement.data.route
                notification_data["screen"] = route
                send_fcm_notification_to_gym_members_by_filter(
                    gym_id=announcement.gym_id,
                    title=announcement.title,
                    body=announcement.message,
                    send_to=announcement.send_to.value,
                    data=notification_data,
                    session=self.session,
                    member_ids=announcement.member_ids,
                )
            except Exception as e:
                logger.error(
                    f"[NOTIFICATION DEBUG] Exception occurred while sending FCM notifications for announcement {db_announcement.id}: {str(e)}",
                    exc_info=True
                )
        
        return AnnouncementResponse.model_validate(self._announcement_to_response(db_announcement))

    def get_announcements_by_gym(self, gym_id: str) -> List[AnnouncementResponse]:
        """Get all announcements for a gym"""
        stmt = select(Announcement).where(Announcement.gym_id == gym_id)
        stmt = stmt.order_by(Announcement.created_at.desc())
        
        announcements = self.session.exec(stmt).all()
        return [AnnouncementResponse.model_validate(self._announcement_to_response(a)) for a in announcements]

    def _announcement_to_response(self, a: Announcement) -> dict:
        d = a.model_dump()
        d["send_to"] = a.send_to.value if a.send_to else None
        return d

    def create_platform_announcement(
        self, payload: PlatformAnnouncementCreate, user_id: str
    ) -> AnnouncementResponse:
        """Create a platform-level announcement and send FCM to the selected audience."""
        from app.core.exceptions import ValidationError
        from app.utils.fcm_notification import send_fcm_notification_to_platform_audience

        send_to = payload.send_to
        if send_to == SendToType.SPECIFIC_GYM and not payload.gym_id:
            raise ValidationError(detail="gym_id is required when send_to is 'Specific Gym'")
        if send_to == SendToType.SPECIFIC_MEMBER and (not payload.member_ids or len(payload.member_ids) == 0):
            raise ValidationError(detail="member_ids is required when send_to is 'Specific Member'")

        db_announcement = Announcement(
            gym_id=payload.gym_id,
            user_id=user_id,
            title=payload.title,
            message=payload.message,
            is_active=True,
            send_to=send_to,
            member_ids=payload.member_ids,
        )
        self.session.add(db_announcement)
        self.session.commit()
        self.session.refresh(db_announcement)

        try:
            notification_data = {
                "announcement_id": db_announcement.id,
                "type": "announcement",
            }
            if payload.gym_id:
                notification_data["gym_id"] = payload.gym_id
            route = "/gym-details"
            if payload.data and payload.data.route:
                route = payload.data.route
            notification_data["screen"] = route
            send_fcm_notification_to_platform_audience(
                send_to=send_to.value,
                title=payload.title,
                body=payload.message,
                data=notification_data,
                session=self.session,
                gym_id=payload.gym_id,
                member_ids=payload.member_ids,
            )
        except Exception as e:
            logger.error(
                f"[NOTIFICATION DEBUG] Exception sending FCM for platform announcement {db_announcement.id}: {str(e)}",
                exc_info=True,
            )

        return AnnouncementResponse.model_validate(self._announcement_to_response(db_announcement))

    def get_announcements_for_user(self, current_user: User) -> List[AnnouncementResponse]:
        """Return only announcements relevant to the logged-in user (user-specific filtering)."""

        role_name = None
        if current_user.role_id:
            from app.models.role import Role
            role = self.session.exec(select(Role).where(Role.id == current_user.role_id)).first()
            role_name = role.name if role else None

        results: List[AnnouncementResponse] = []
        stmt = (
            select(Announcement)
            .where(Announcement.is_active == True)
            .order_by(Announcement.created_at.desc())
        )
        all_announcements = self.session.exec(stmt).all()

        for a in all_announcements:
            # Platform-wide announcements (gym_id is None)
            if a.gym_id is None:
                if a.send_to == SendToType.ALL_USERS:
                    results.append(AnnouncementResponse.model_validate(self._announcement_to_response(a)))
                    continue
                if a.send_to == SendToType.OWNERS and role_name == "ADMIN":
                    results.append(AnnouncementResponse.model_validate(self._announcement_to_response(a)))
                    continue
                if a.send_to == SendToType.MEMBERS and role_name == "MEMBER":
                    results.append(AnnouncementResponse.model_validate(self._announcement_to_response(a)))
                    continue
                if a.send_to == SendToType.SPECIFIC_MEMBER and a.member_ids and current_user.id in a.member_ids:
                    results.append(AnnouncementResponse.model_validate(self._announcement_to_response(a)))
                    continue
                continue

            # Gym-scoped announcements: only if user belongs to this gym
            if current_user.gym_id != a.gym_id:
                continue
            if a.send_to == SendToType.ALL:
                results.append(AnnouncementResponse.model_validate(self._announcement_to_response(a)))
                continue
            if a.send_to == SendToType.SPECIFIC_GYM:
                # Platform announcement targeting this gym
                results.append(AnnouncementResponse.model_validate(self._announcement_to_response(a)))
                continue
            if a.send_to == SendToType.SPECIFIC_MEMBERS and a.member_ids and current_user.id in a.member_ids:
                results.append(AnnouncementResponse.model_validate(self._announcement_to_response(a)))

        return results

    def get_announcement_by_id(self, announcement_id: str) -> AnnouncementResponse:
        """Get a single announcement by ID"""
        stmt = select(Announcement).where(Announcement.id == announcement_id)
        announcement = self.session.exec(stmt).first()
        if not announcement:
            raise NotFoundError(detail=f"Announcement with id {announcement_id} not found")
        return AnnouncementResponse.model_validate(self._announcement_to_response(announcement))

    def update_announcement(
        self,
        announcement_id: str,
        announcement_update: AnnouncementUpdate
    ) -> AnnouncementResponse:
        """Update an announcement"""
        stmt = select(Announcement).where(Announcement.id == announcement_id)
        db_announcement = self.session.exec(stmt).first()
        if not db_announcement:
            raise NotFoundError(detail=f"Announcement with id {announcement_id} not found")
        
        update_data = announcement_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(db_announcement, field, value)
        
        db_announcement.updated_at = datetime.now()
        
        self.session.commit()
        self.session.refresh(db_announcement)
        return AnnouncementResponse.model_validate(self._announcement_to_response(db_announcement))

    def delete_announcement(self, announcement_id: str) -> None:
        """Delete an announcement"""
        stmt = select(Announcement).where(Announcement.id == announcement_id)
        announcement = self.session.exec(stmt).first()
        if not announcement:
            raise NotFoundError(detail=f"Announcement with id {announcement_id} not found")
        
        self.session.delete(announcement)
        self.session.commit()
        return None

