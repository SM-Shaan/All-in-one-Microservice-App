"""
Saga Orchestrator
=================

Manages the order saga workflow.

Saga Pattern (Orchestration):
A central orchestrator coordinates all saga steps.
If a step fails, it triggers compensation.

Order Saga Flow:
1. Create Order
2. Verify User (call User Service)
3. Check Products (call Product Service)
4. Reserve Inventory (simulated for now)
5. Process Payment (simulated for now)
6. Confirm Order

If any step fails:
- Compensation is triggered
- Previous steps are rolled back
- Order is marked as cancelled
"""

from uuid import uuid4
from datetime import datetime
from typing import Optional
import httpx

from app.models.order import (
    Order,
    OrderStatus,
    SagaState,
    SagaStatus,
    SagaStep,
    OrderItem
)
from app.core.config import settings


class SagaOrchestrator:
    """
    Orchestrates the order saga.

    Coordinates all services involved in order processing.
    """

    def __init__(self, http_client: httpx.AsyncClient):
        """
        Initialize saga orchestrator.

        Args:
            http_client: HTTP client for calling other services
        """
        self.http_client = http_client
        self.user_service_url = settings.user_service_url
        self.product_service_url = settings.product_service_url

    async def execute_order_saga(self, order: Order) -> tuple[bool, Optional[str]]:
        """
        Execute the complete order saga.

        Args:
            order: Order to process

        Returns:
            tuple[bool, Optional[str]]: (success, error_message)

        Example:
            success, error = await orchestrator.execute_order_saga(order)
            if success:
                print("Order confirmed!")
            else:
                print(f"Order failed: {error}")
        """
        # Initialize saga state
        saga_state = SagaState(
            saga_id=f"saga-{uuid4()}",
            order_id=str(order.id),
            status=SagaStatus.STARTED
        )

        print(f"\n{'='*60}")
        print(f"🎬 STARTING ORDER SAGA: {saga_state.saga_id}")
        print(f"{'='*60}\n")

        order.saga_id = saga_state.saga_id
        order.saga_status = SagaStatus.IN_PROGRESS

        try:
            # Step 1: Verify User
            success = await self._verify_user(saga_state, order)
            if not success:
                await self._compensate(saga_state, order)
                return False, saga_state.error_message

            # Step 2: Check Products and Get Details
            success = await self._check_products(saga_state, order)
            if not success:
                await self._compensate(saga_state, order)
                return False, saga_state.error_message

            # Step 3: Reserve Inventory (Simulated)
            success = await self._reserve_inventory(saga_state, order)
            if not success:
                await self._compensate(saga_state, order)
                return False, saga_state.error_message

            # Step 4: Process Payment (Simulated)
            success = await self._process_payment(saga_state, order)
            if not success:
                await self._compensate(saga_state, order)
                return False, saga_state.error_message

            # Step 5: Confirm Order
            success = await self._confirm_order(saga_state, order)
            if not success:
                await self._compensate(saga_state, order)
                return False, saga_state.error_message

            # All steps completed!
            saga_state.status = SagaStatus.COMPLETED
            saga_state.completed_at = datetime.utcnow()

            order.status = OrderStatus.CONFIRMED
            order.saga_status = SagaStatus.COMPLETED
            order.confirmed_at = datetime.utcnow()

            print(f"\n{'='*60}")
            print(f"✅ SAGA COMPLETED SUCCESSFULLY")
            print(f"{'='*60}\n")

            return True, None

        except Exception as e:
            print(f"❌ Saga execution error: {e}")
            saga_state.status = SagaStatus.FAILED
            saga_state.error_message = str(e)
            await self._compensate(saga_state, order)
            return False, str(e)

    # ========================================================================
    # Saga Steps
    # ========================================================================

    async def _verify_user(self, saga_state: SagaState, order: Order) -> bool:
        """
        Step 1: Verify user exists.

        Calls User Service to check if user exists and is active.
        """
        step = SagaStep.VERIFY_USER
        saga_state.mark_step_started(step)

        print(f"🔄 Step 1: Verifying user {order.user_id}...")

        try:
            # Call User Service
            url = f"{self.user_service_url}/api/v1/users/{order.user_id}"
            response = await self.http_client.get(url, timeout=5.0)

            if response.status_code == 404:
                saga_state.mark_step_failed(step, "User not found")
                print(f"❌ User not found")
                return False

            if response.status_code != 200:
                saga_state.mark_step_failed(step, f"User service error: {response.status_code}")
                print(f"❌ User service error")
                return False

            user_data = response.json()

            if not user_data.get("is_active"):
                saga_state.mark_step_failed(step, "User is not active")
                print(f"❌ User is not active")
                return False

            saga_state.mark_step_completed(step)
            print(f"✅ User verified: {user_data.get('email')}")
            return True

        except httpx.TimeoutException:
            saga_state.mark_step_failed(step, "User service timeout")
            print(f"❌ User service timeout")
            return False
        except Exception as e:
            saga_state.mark_step_failed(step, str(e))
            print(f"❌ Error verifying user: {e}")
            return False

    async def _check_products(self, saga_state: SagaState, order: Order) -> bool:
        """
        Step 2: Check products exist and get details.

        Calls Product Service to verify products and get pricing.
        """
        step = SagaStep.CHECK_PRODUCTS
        saga_state.mark_step_started(step)

        print(f"🔄 Step 2: Checking {len(order.items)} products...")

        try:
            order_items = []
            subtotal = 0.0

            for item in order.items:
                # Call Product Service
                url = f"{self.product_service_url}/api/v1/products/{item.product_id}"
                response = await self.http_client.get(url, timeout=5.0)

                if response.status_code == 404:
                    saga_state.mark_step_failed(step, f"Product {item.product_id} not found")
                    print(f"❌ Product not found: {item.product_id}")
                    return False

                if response.status_code != 200:
                    saga_state.mark_step_failed(step, "Product service error")
                    print(f"❌ Product service error")
                    return False

                product = response.json()

                # Check stock
                if product.get("stock", 0) < item.quantity:
                    saga_state.mark_step_failed(
                        step,
                        f"Insufficient stock for {product['name']}"
                    )
                    print(f"❌ Insufficient stock for {product['name']}")
                    return False

                # Calculate pricing
                unit_price = product["price"]
                subtotal_item = unit_price * item.quantity
                subtotal += subtotal_item

                # Create order item with details
                order_items.append(OrderItem(
                    product_id=item.product_id,
                    product_name=product["name"],
                    quantity=item.quantity,
                    unit_price=unit_price,
                    subtotal=subtotal_item
                ))

                print(f"   ✓ {product['name']}: ${unit_price} x {item.quantity}")

            # Update order with product details
            order.items = order_items
            order.subtotal = subtotal
            order.tax = subtotal * 0.08  # 8% tax
            order.shipping_cost = 10.0 if subtotal < 100 else 0.0  # Free shipping > $100
            order.total = order.subtotal + order.tax + order.shipping_cost

            saga_state.mark_step_completed(step)
            print(f"✅ Products verified. Total: ${order.total:.2f}")
            return True

        except httpx.TimeoutException:
            saga_state.mark_step_failed(step, "Product service timeout")
            print(f"❌ Product service timeout")
            return False
        except Exception as e:
            saga_state.mark_step_failed(step, str(e))
            print(f"❌ Error checking products: {e}")
            return False

    async def _reserve_inventory(self, saga_state: SagaState, order: Order) -> bool:
        """
        Step 3: Reserve inventory.

        In a real system, this would call Inventory Service.
        For now, we simulate it.
        """
        step = SagaStep.RESERVE_INVENTORY
        saga_state.mark_step_started(step)

        print(f"🔄 Step 3: Reserving inventory...")

        try:
            # Simulate inventory reservation
            # In real system: Call Inventory Service API
            import asyncio
            await asyncio.sleep(0.5)  # Simulate network call

            # Simulated success
            saga_state.mark_step_completed(step)
            print(f"✅ Inventory reserved")
            return True

        except Exception as e:
            saga_state.mark_step_failed(step, str(e))
            print(f"❌ Error reserving inventory: {e}")
            return False

    async def _process_payment(self, saga_state: SagaState, order: Order) -> bool:
        """
        Step 4: Process payment.

        In a real system, this would call Payment Service.
        For now, we simulate it.
        """
        step = SagaStep.PROCESS_PAYMENT
        saga_state.mark_step_started(step)

        print(f"🔄 Step 4: Processing payment (${order.total:.2f})...")

        try:
            # Simulate payment processing
            # In real system: Call Payment Service API
            import asyncio
            await asyncio.sleep(1.0)  # Simulate payment gateway

            # Simulated success (90% success rate for demo)
            import random
            if random.random() < 0.9:
                saga_state.mark_step_completed(step)
                print(f"✅ Payment processed: ${order.total:.2f}")
                return True
            else:
                saga_state.mark_step_failed(step, "Payment declined")
                print(f"❌ Payment declined")
                return False

        except Exception as e:
            saga_state.mark_step_failed(step, str(e))
            print(f"❌ Error processing payment: {e}")
            return False

    async def _confirm_order(self, saga_state: SagaState, order: Order) -> bool:
        """
        Step 5: Confirm order.

        Final step - mark order as confirmed.
        """
        step = SagaStep.CONFIRM_ORDER
        saga_state.mark_step_started(step)

        print(f"🔄 Step 5: Confirming order...")

        try:
            # Order confirmation logic
            order.status = OrderStatus.CONFIRMED
            order.confirmed_at = datetime.utcnow()

            saga_state.mark_step_completed(step)
            print(f"✅ Order confirmed!")
            return True

        except Exception as e:
            saga_state.mark_step_failed(step, str(e))
            print(f"❌ Error confirming order: {e}")
            return False

    # ========================================================================
    # Compensation (Rollback)
    # ========================================================================

    async def _compensate(self, saga_state: SagaState, order: Order):
        """
        Compensate (rollback) completed saga steps.

        This runs when a saga step fails.
        We need to undo all previous successful steps.

        Example:
        - Payment failed
        - Compensation: Release inventory
        - Compensation: Cancel order
        """
        print(f"\n{'='*60}")
        print(f"⚠️ SAGA FAILED - STARTING COMPENSATION")
        print(f"{'='*60}\n")

        saga_state.status = SagaStatus.COMPENSATING

        # Compensate in reverse order
        for step_state in reversed(saga_state.steps):
            if step_state.status == "completed" and not step_state.compensation_performed:
                await self._compensate_step(step_state.step, order)
                step_state.compensation_performed = True

        # Mark order as cancelled
        order.status = OrderStatus.CANCELLED
        order.saga_status = SagaStatus.COMPENSATED
        order.cancelled_at = datetime.utcnow()
        order.cancellation_reason = saga_state.error_message

        saga_state.status = SagaStatus.COMPENSATED

        print(f"\n{'='*60}")
        print(f"✅ COMPENSATION COMPLETED")
        print(f"{'='*60}\n")

    async def _compensate_step(self, step: SagaStep, order: Order):
        """Compensate a specific step"""
        print(f"🔄 Compensating: {step.value}")

        if step == SagaStep.RESERVE_INVENTORY:
            # Release inventory reservation
            print(f"   → Releasing inventory reservation")
            # In real system: Call Inventory Service to release

        elif step == SagaStep.PROCESS_PAYMENT:
            # Refund payment
            print(f"   → Refunding payment")
            # In real system: Call Payment Service to refund

        print(f"   ✅ Compensation complete for {step.value}")
