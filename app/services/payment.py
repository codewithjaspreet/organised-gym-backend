from sqlmodel import select, and_, func
from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import List
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.payments import Payment
from app.models.membership import Membership
from app.models.plan import Plan
from app.models.gym import Gym
from app.schemas.payments import (
    PaymentCreate, PaymentResponse, PaymentUpdate, MemberPaymentCreate, 
    PaymentStatusUpdate, PaymentStatusType, PendingPaymentResponse, PendingPaymentListResponse
)
from app.schemas.user import CurrentPlanResponse


class PaymentService:

    def __init__(self, session: SessionDep):
        self.session = session

    def create_payment(self, payment: PaymentCreate) -> PaymentResponse:
        db_payment = Payment(
            user_id=payment.user_id,
            membership_id=payment.membership_id,
            gym_id=payment.gym_id,
            amount=payment.amount,
            proof_url=payment.proof_url,
            status=payment.status,
            verified_by=payment.verified_by
        )
        self.session.add(db_payment)
        self.session.commit()
        self.session.refresh(db_payment)

        return PaymentResponse.model_validate(db_payment.model_dump())

    def get_payment(self, payment_id: str) -> PaymentResponse:
        stmt = select(Payment).where(Payment.id == payment_id)
        payment = self.session.exec(stmt).first()
        if not payment:
            raise NotFoundError(detail=f"Payment with id {payment_id} not found")

        return PaymentResponse.model_validate(payment)

    def update_payment(self, payment_id: str, payment_update: PaymentUpdate) -> PaymentResponse:
        stmt = select(Payment).where(Payment.id == payment_id)
        payment = self.session.exec(stmt).first()
        if not payment:
            raise NotFoundError(detail=f"Payment with id {payment_id} not found")

        # Update only provided fields
        update_data = payment_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payment, field, value)

        self.session.commit()
        self.session.refresh(payment)

        return PaymentResponse.model_validate(payment)

    def delete_payment(self, payment_id: str) -> None:
        stmt = select(Payment).where(Payment.id == payment_id)
        payment = self.session.exec(stmt).first()
        if not payment:
            raise NotFoundError(detail=f"Payment with id {payment_id} not found")

        self.session.delete(payment)
        self.session.commit()
        return None

    def create_member_payment(
        self,
        user_id: str,
        payment_data: MemberPaymentCreate
    ) -> PaymentResponse:
        """Create payment from plan_id, find membership, and send notification to owner"""
        # Verify plan exists
        plan_stmt = select(Plan).where(Plan.id == payment_data.plan_id)
        plan = self.session.exec(plan_stmt).first()
        if not plan:
            raise NotFoundError(detail=f"Plan with id {payment_data.plan_id} not found")

        # Get user's gym_id
        from app.models.user import User
        user_stmt = select(User).where(User.id == user_id)
        user = self.session.exec(user_stmt).first()
        if not user:
            raise NotFoundError(detail=f"User with id {user_id} not found")
        
        if not user.gym_id:
            raise NotFoundError(detail="User has no gym assigned")

        # Find active membership for this user and plan
        today = date.today()
        membership_stmt = select(Membership).where(
            and_(
                Membership.user_id == user_id,
                Membership.plan_id == payment_data.plan_id,
                Membership.gym_id == user.gym_id,
                Membership.status == "active"
            )
        ).order_by(Membership.end_date.desc())
        membership = self.session.exec(membership_stmt).first()

        if not membership:
            raise NotFoundError(detail="No active membership found for this plan")

        # Get amount from membership (new_price if exists, otherwise from plan)
        payment_amount = membership.new_price if membership.new_price is not None else plan.price

        # Create payment
        db_payment = Payment(
            user_id=user_id,
            membership_id=membership.id,
            gym_id=user.gym_id,
            amount=payment_amount,
            proof_url=payment_data.proof_url,
            status="pending"
        )
        self.session.add(db_payment)
        self.session.commit()
        self.session.refresh(db_payment)

        # Send FCM notification to gym owner
        try:
            from app.utils.fcm_notification import send_fcm_notification_to_user
            from app.models.gym import Gym
            
            # Get gym owner
            gym_stmt = select(Gym).where(Gym.id == user.gym_id)
            gym = self.session.exec(gym_stmt).first()
            
            if gym and gym.owner_id:
                notification_title = "New Payment Received"
                notification_message = f"{user.name} made a payment of ₹{payment_amount} for plan {plan.name}"
                
                notification_data = {
                    "type": "payment",
                    "payment_id": db_payment.id,
                    "gym_id": user.gym_id,
                    "screen": "/payments"
                }
                
                # Send FCM notification
                send_fcm_notification_to_user(
                    user_id=gym.owner_id,
                    title=notification_title,
                    body=notification_message,
                    data=notification_data,
                    session=self.session
                )
        except Exception as e:
            # Log error but don't fail payment creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send payment notification to owner: {str(e)}")

        return PaymentResponse.model_validate(db_payment.model_dump())

    def update_payment_status(
        self,
        payment_status_update: PaymentStatusUpdate,
        verified_by: str
    ) -> PaymentResponse:
        """Approve or reject payment and send notification to member"""
        stmt = select(Payment).where(Payment.id == payment_status_update.payment_id)
        payment = self.session.exec(stmt).first()
        if not payment:
            raise NotFoundError(detail=f"Payment with id {payment_status_update.payment_id} not found")

        # Update payment status based on the status type
        if payment_status_update.status == PaymentStatusType.APPROVE:
            payment.status = "verified"
            payment.verified_by = verified_by
        elif payment_status_update.status == PaymentStatusType.REJECT:
            payment.status = "rejected"
            payment.verified_by = verified_by
        else:
            raise ValueError(f"Invalid status: {payment_status_update.status}")

        self.session.commit()
        self.session.refresh(payment)

        # Send FCM notification to member
        try:
            from app.utils.fcm_notification import send_fcm_notification_to_user
            
            if payment_status_update.status == PaymentStatusType.APPROVE:
                notification_title = "Payment Verified"
                notification_message = f"Thank you! Your payment of ₹{payment.amount} has been verified successfully."
                notification_type = "payment_verified"
            else:  # REJECT
                notification_title = "Payment Rejected"
                notification_message = f"Your payment of ₹{payment.amount} has been rejected. Please contact the gym for more details."
                notification_type = "payment_rejected"
            
            notification_data = {
                "type": notification_type,
                "payment_id": payment.id,
                "gym_id": payment.gym_id,
                "screen": "/payments"
            }
            
            # Send FCM notification
            send_fcm_notification_to_user(
                user_id=payment.user_id,
                title=notification_title,
                body=notification_message,
                data=notification_data,
                session=self.session
            )
        except Exception as e:
            # Log error but don't fail payment status update
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send payment status notification to member: {str(e)}")

        return PaymentResponse.model_validate(payment.model_dump())

    def get_pending_payments(
        self,
        gym_id: str,
        filter_status: str = "pending",
        page: int = 1,
        page_size: int = 20
    ) -> PendingPaymentListResponse:
        """
        Get payments for a gym with pagination and status filtering.
        Returns payment details with member's current plan information.
        
        Args:
            gym_id: Gym ID
            filter_status: Filter by status - "all", "approved", "rejected", or "pending" (default)
            page: Page number
            page_size: Items per page
        """
        from app.models.user import User
        
        # Build status filter condition
        status_conditions = []
        if filter_status == "all":
            # No status filter - get all payments
            status_conditions = [Payment.gym_id == gym_id]
        elif filter_status == "approved":
            # Get verified/approved payments
            status_conditions = [
                Payment.gym_id == gym_id,
                Payment.status == "verified"
            ]
        elif filter_status == "rejected":
            # Get rejected payments
            status_conditions = [
                Payment.gym_id == gym_id,
                Payment.status == "rejected"
            ]
        else:
            # Default: pending payments
            status_conditions = [
                Payment.gym_id == gym_id,
                Payment.status == "pending"
            ]
        
        # Base query: payments for the gym with status filter
        stmt = select(Payment).where(
            and_(*status_conditions)
        ).order_by(Payment.created_at.desc())
        
        # Get total count
        count_stmt = select(func.count(Payment.id)).where(
            and_(*status_conditions)
        )
        total = self.session.exec(count_stmt).first() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.limit(page_size).offset(offset)
        
        # Execute query
        payments = self.session.exec(stmt).all()
        
        # Build response with current plan info for each member
        # Optimize: Get all unique user_ids first, then fetch users, memberships and plans in bulk
        user_ids = list(set([payment.user_id for payment in payments]))
        
        # Fetch all users in one query
        users_stmt = select(User).where(User.id.in_(user_ids))
        all_users = self.session.exec(users_stmt).all()
        users_by_id = {user.id: user for user in all_users}
        
        # Fetch all active memberships for these users in one query
        today = date.today()
        memberships_stmt = select(Membership).where(
            and_(
                Membership.user_id.in_(user_ids),
                Membership.gym_id == gym_id,
                Membership.end_date >= today,
                Membership.status == "active"
            )
        ).order_by(Membership.user_id, Membership.end_date.desc())
        all_memberships = self.session.exec(memberships_stmt).all()
        
        # Group memberships by user_id (get the most recent one per user)
        memberships_by_user = {}
        for membership in all_memberships:
            if membership.user_id not in memberships_by_user:
                memberships_by_user[membership.user_id] = membership
        
        # Get all plan_ids and fetch plans in one query
        plan_ids = list(set([m.plan_id for m in memberships_by_user.values() if m.plan_id]))
        plans_by_id = {}
        if plan_ids:
            plans_stmt = select(Plan).where(Plan.id.in_(plan_ids))
            all_plans = self.session.exec(plans_stmt).all()
            plans_by_id = {plan.id: plan for plan in all_plans}
        
        # Build response
        pending_payments = []
        ist = ZoneInfo("Asia/Kolkata")
        
        for payment in payments:
            # Format payment_at in Indian format
            payment_at = payment.created_at
            if payment_at.tzinfo is None:
                payment_at = payment_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(ist)
            else:
                payment_at = payment_at.astimezone(ist)
            payment_at_str = payment_at.strftime("%d-%m-%Y %H:%M:%S")
            
            # Get current plan for the member
            current_plan = None
            membership = memberships_by_user.get(payment.user_id)
            
            if membership:
                plan = plans_by_id.get(membership.plan_id)
                
                if plan:
                    # Use new_price if available, otherwise use plan.price
                    total_price = float(membership.new_price) if membership.new_price else float(plan.price)
                    days_left = (membership.end_date - today).days
                    if days_left <= 7:
                        status = "expiring_soon"
                    else:
                        status = "active"
                    
                    current_plan = CurrentPlanResponse(
                        plan_id=plan.id,
                        plan_name=plan.name,
                        expiry_date=membership.end_date.isoformat(),
                        monthly_price=round(total_price, 2),
                        status=status,
                        days_left=days_left
                    )
            
            # Get user_name and name
            user = users_by_id.get(payment.user_id)
            user_name = user.user_name if user else ""
            name = user.name if user else ""
            
            # Map payment status to response status
            if payment.status == "verified":
                payment_status = "approved"
            elif payment.status == "rejected":
                payment_status = "rejected"
            else:
                payment_status = "pending"
            
            # Note: remarks is not stored in Payment model, so returning None
            pending_payments.append(PendingPaymentResponse(
                payment_id=payment.id,
                user_id=payment.user_id,
                user_name=user_name,
                name=name,
                proof_url=payment.proof_url,
                remarks=None,  # Remarks not stored in Payment model currently
                payment_at=payment_at_str,
                current_plan=current_plan,
                status=payment_status
            ))
        
        has_next = (page * page_size) < total
        
        return PendingPaymentListResponse(
            payments=pending_payments,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next
        )

