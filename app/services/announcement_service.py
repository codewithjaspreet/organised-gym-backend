import logging
from typing import List
from datetime import datetime
from sqlmodel import select
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.announcement import Announcement, SendToType
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse, AnnouncementUpdate

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
        
        return AnnouncementResponse.model_validate(db_announcement.model_dump())

    def get_announcements_by_gym(self, gym_id: str) -> List[AnnouncementResponse]:
        """Get all announcements for a gym"""
        stmt = select(Announcement).where(Announcement.gym_id == gym_id)
        stmt = stmt.order_by(Announcement.created_at.desc())
        
        announcements = self.session.exec(stmt).all()
        return [AnnouncementResponse.model_validate(a.model_dump()) for a in announcements]

    def get_announcement_by_id(self, announcement_id: str) -> AnnouncementResponse:
        """Get a single announcement by ID"""
        stmt = select(Announcement).where(Announcement.id == announcement_id)
        announcement = self.session.exec(stmt).first()
        if not announcement:
            raise NotFoundError(detail=f"Announcement with id {announcement_id} not found")
        
        return AnnouncementResponse.model_validate(announcement.model_dump())

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
        
        return AnnouncementResponse.model_validate(db_announcement.model_dump())

    def delete_announcement(self, announcement_id: str) -> None:
        """Delete an announcement"""
        stmt = select(Announcement).where(Announcement.id == announcement_id)
        announcement = self.session.exec(stmt).first()
        if not announcement:
            raise NotFoundError(detail=f"Announcement with id {announcement_id} not found")
        
        self.session.delete(announcement)
        self.session.commit()
        return None

