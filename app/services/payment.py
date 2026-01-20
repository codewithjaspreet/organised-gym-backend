from sqlmodel import select, and_
from datetime import date
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.payments import Payment
from app.models.membership import Membership
from app.models.plan import Plan
from app.models.gym import Gym
from app.schemas.payments import PaymentCreate, PaymentResponse, PaymentUpdate, MemberPaymentCreate, PaymentStatusUpdate, PaymentStatusType


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

