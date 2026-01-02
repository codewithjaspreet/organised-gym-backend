from typing import List
from datetime import datetime
from sqlmodel import select
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.announcement import Announcement
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse, AnnouncementUpdate


class AnnouncementService:

    def __init__(self, session: SessionDep):
        self.session = session

    def create_announcement(self, announcement: AnnouncementCreate) -> AnnouncementResponse:
        """Create a new announcement"""
        db_announcement = Announcement(
            gym_id=announcement.gym_id,
            user_id=announcement.user_id,
            title=announcement.title,
            message=announcement.message,
            is_active=announcement.is_active
        )
        self.session.add(db_announcement)
        self.session.commit()
        self.session.refresh(db_announcement)
        
        return AnnouncementResponse.model_validate(db_announcement)

    def get_announcements_by_gym(self, gym_id: str) -> List[AnnouncementResponse]:
        """Get all announcements for a gym"""
        stmt = select(Announcement).where(Announcement.gym_id == gym_id)
        stmt = stmt.order_by(Announcement.created_at.desc())
        
        announcements = self.session.exec(stmt).all()
        return [AnnouncementResponse.model_validate(a) for a in announcements]

    def get_announcement_by_id(self, announcement_id: str) -> AnnouncementResponse:
        """Get a single announcement by ID"""
        stmt = select(Announcement).where(Announcement.id == announcement_id)
        announcement = self.session.exec(stmt).first()
        if not announcement:
            raise NotFoundError(detail=f"Announcement with id {announcement_id} not found")
        
        return AnnouncementResponse.model_validate(announcement)

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
        
        return AnnouncementResponse.model_validate(db_announcement)

    def delete_announcement(self, announcement_id: str) -> None:
        """Delete an announcement"""
        stmt = select(Announcement).where(Announcement.id == announcement_id)
        announcement = self.session.exec(stmt).first()
        if not announcement:
            raise NotFoundError(detail=f"Announcement with id {announcement_id} not found")
        
        self.session.delete(announcement)
        self.session.commit()
        return None

