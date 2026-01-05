from sqlmodel import select
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.billing import Payment
from app.schemas.billing import PaymentCreate, PaymentResponse, PaymentUpdate


class BillingService:

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

        return PaymentResponse.model_validate(db_payment)

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

    # approve payment 

