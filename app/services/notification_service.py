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
        """Create a new notification"""
        db_notification = Notification(
            user_id=notification.user_id,
            type="general",  # Default type, can be customized
            title=notification.title,
            message=notification.message,
            status="pending"  # Default status
        )
        self.session.add(db_notification)
        self.session.commit()
        self.session.refresh(db_notification)
        
        return NotificationResponse.model_validate(db_notification)

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
        
        notification_responses = [NotificationResponse.model_validate(n) for n in notifications]
        
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
        
        notification_responses = [NotificationResponse.model_validate(n) for n in notifications]
        
        return NotificationListResponse(notifications=notification_responses, total=total)

    def get_notification_by_id(self, notification_id: str) -> NotificationResponse:
        """Get a single notification by ID"""
        stmt = select(Notification).where(Notification.id == notification_id)
        notification = self.session.exec(stmt).first()
        if not notification:
            raise NotFoundError(detail=f"Notification with id {notification_id} not found")
        
        return NotificationResponse.model_validate(notification)
