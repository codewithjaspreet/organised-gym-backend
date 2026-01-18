from typing import List, Optional
from sqlmodel import select
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse
)


class NotificationService:

    def __init__(self, session: SessionDep):
        self.session = session

    def create_notification(self, notification: NotificationCreate) -> NotificationResponse:
        """Create notification, apply filter, send FCM, and save single gym-level record"""
        from app.utils.fcm_notification import send_fcm_notification_to_gym_members_by_filter
        from app.models.gym import Gym
        
        # Get gym owner_id for the notification record
        gym_stmt = select(Gym).where(Gym.id == notification.gym_id)
        gym = self.session.exec(gym_stmt).first()
        if not gym:
            raise NotFoundError(detail=f"Gym with id {notification.gym_id} not found")
        
        # Prepare notification data
        notification_data = {
            "type": "notification",
            "gym_id": notification.gym_id,
            "screen": notification.screen or "/notifications"
        }
        
        # Get filtered users and send notifications
        notification_results = send_fcm_notification_to_gym_members_by_filter(
            gym_id=notification.gym_id,
            title=notification.title,
            body=notification.message,
            send_to=notification.send_to.value,
            data=notification_data,
            session=self.session
        )
        
        # Calculate success status
        successful_count = sum(1 for r in notification_results if r.get("success", False))
        total_count = len(notification_results)
        status = "sent" if successful_count > 0 else "failed" if total_count > 0 else "no_recipients"
        
        # Save single gym-level notification record
        db_notification = Notification(
            user_id=gym.owner_id,  # Use gym owner as placeholder for gym-level notification
            type=notification.send_to.value.lower().replace(" ", "_"),
            title=notification.title,
            message=notification.message,
            status=status
        )
        self.session.add(db_notification)
        self.session.commit()
        self.session.refresh(db_notification)
        
        return NotificationResponse.model_validate(db_notification.model_dump())

    def get_notifications_by_user(
        self,
        user_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> NotificationListResponse:
        """Get notifications for a specific user"""
        stmt = select(Notification).where(Notification.user_id == user_id)
        stmt = stmt.order_by(Notification.sent_at.desc())
        
        if limit:
            stmt = stmt.limit(limit).offset(offset)
        
        notifications = self.session.exec(stmt).all()
        total = len(list(self.session.exec(select(Notification).where(Notification.user_id == user_id))))
        
        notification_responses = [NotificationResponse.model_validate(n.model_dump()) for n in notifications]
        
        return NotificationListResponse(notifications=notification_responses, total=total)

    def get_notifications_by_gym(
        self,
        gym_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> NotificationListResponse:
        """Get notifications for all users in a gym"""
        from app.models.user import User
        
        # Get all user IDs in the gym
        user_stmt = select(User.id).where(User.gym_id == gym_id)
        user_ids_result = self.session.exec(user_stmt).all()
        user_ids = [user_id for user_id in user_ids_result] if user_ids_result else []
        
        if not user_ids:
            return NotificationListResponse(notifications=[], total=0)
        
        stmt = select(Notification).where(Notification.user_id.in_(user_ids))
        stmt = stmt.order_by(Notification.sent_at.desc())
        
        if limit:
            stmt = stmt.limit(limit).offset(offset)
        
        notifications = self.session.exec(stmt).all()
        total = len(list(self.session.exec(select(Notification).where(Notification.user_id.in_(user_ids)))))
        
        notification_responses = [NotificationResponse.model_validate(n.model_dump()) for n in notifications]
        
        return NotificationListResponse(notifications=notification_responses, total=total)

    def get_notification_by_id(self, notification_id: str) -> NotificationResponse:
        """Get a single notification by ID"""
        stmt = select(Notification).where(Notification.id == notification_id)
        notification = self.session.exec(stmt).first()
        if not notification:
            raise NotFoundError(detail=f"Notification with id {notification_id} not found")
        
        return NotificationResponse.model_validate(notification.model_dump())
