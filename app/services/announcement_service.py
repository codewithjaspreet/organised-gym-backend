import logging
from typing import List
from datetime import datetime
from sqlmodel import select
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.announcement import Announcement
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
        if announcement.send_to.value == "Specific Members":
            if not announcement.member_ids or len(announcement.member_ids) == 0:
                raise ValidationError(detail="member_ids is required when send_to is 'Specific Members'")
        
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
        
        if announcement.is_active:
            try:
                logger.info(
                    f"[NOTIFICATION DEBUG] Starting notification process for announcement {db_announcement.id}. "
                    f"Gym ID: {announcement.gym_id}, Send To: {announcement.send_to.value}, "
                    f"Member IDs: {announcement.member_ids if announcement.member_ids else 'None'}"
                )
                
                # Build data payload with dynamic route from data object
                notification_data = {
                    "announcement_id": db_announcement.id,
                    "type": "announcement",
                    "gym_id": announcement.gym_id
                }
                
                # Get route from data object, map to 'screen' in FCM payload
                route = "/gym-details"  # default
                if announcement.data and announcement.data.route:
                    route = announcement.data.route
                
                # Map route to 'screen' in FCM notification data
                notification_data["screen"] = route
                
                logger.info(
                    f"[NOTIFICATION DEBUG] Notification payload prepared. "
                    f"Title: '{announcement.title}', Body: '{announcement.message[:50]}...', "
                    f"Data: {notification_data}, Route: {route}"
                )
                
                # Send notifications based on send_to filter
                logger.info(
                    f"[NOTIFICATION DEBUG] Calling send_fcm_notification_to_gym_members_by_filter with "
                    f"gym_id={announcement.gym_id}, send_to={announcement.send_to.value}, "
                    f"member_ids={announcement.member_ids}"
                )
                
                notification_results = send_fcm_notification_to_gym_members_by_filter(
                    gym_id=announcement.gym_id,
                    title=announcement.title,
                    body=announcement.message,
                    send_to=announcement.send_to.value,
                    data=notification_data,
                    session=self.session,
                    member_ids=announcement.member_ids
                )
                
                logger.info(
                    f"[NOTIFICATION DEBUG] Notification function returned {len(notification_results)} results"
                )
                
                # Log notification results
                successful = sum(1 for r in notification_results if r.get("success", False))
                failed = sum(1 for r in notification_results if not r.get("success", False))
                total = len(notification_results)
                
                logger.info(
                    f"[NOTIFICATION DEBUG] Notification results breakdown - "
                    f"Total: {total}, Successful: {successful}, Failed: {failed}"
                )
                
                # Log detailed results for each notification
                for idx, result in enumerate(notification_results, 1):
                    if result.get("success", False):
                        logger.info(
                            f"[NOTIFICATION DEBUG] Result #{idx} - SUCCESS - "
                            f"User ID: {result.get('user_id', 'N/A')}, "
                            f"Device Token: {result.get('device_token', 'N/A')[:20]}..., "
                            f"Response: {result.get('response', {})}"
                        )
                    else:
                        logger.warning(
                            f"[NOTIFICATION DEBUG] Result #{idx} - FAILED - "
                            f"User ID: {result.get('user_id', 'N/A')}, "
                            f"Device Token: {result.get('device_token', 'N/A')[:20]}..., "
                            f"Error: {result.get('error', 'Unknown error')}"
                        )
                
                logger.info(
                    f"Announcement {db_announcement.id} created with send_to='{announcement.send_to.value}'. "
                    f"Notifications sent: {successful}/{total} members"
                )
            except Exception as e:
                # Log error but don't fail announcement creation
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

