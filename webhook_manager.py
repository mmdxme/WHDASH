"""
Webhook Management System
=======================
Enterprise webhook subscription, delivery, and management.

Features:
- Webhook subscriptions with event filtering
- HMAC signature verification
- Delivery with exponential backoff retry
- Parallel and sequential delivery
- Delivery logs and monitoring
- Webhook secret management
- Developer portal support

Usage:
    from webhook_manager import (
        subscribe_webhook, unsubscribe_webhook,
        deliver_webhook, WebhookManager
    )

    # Subscribe to events
    subscribe_webhook(
        url='https://example.com/webhook',
        events=['domain.invoice.created', 'domain.order.*'],
        secret='webhook_secret_123'
    )

    # Manually trigger a delivery
    deliver_webhook('domain.invoice.created', {'invoice_id': 123})
"""

import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
import threading
import queue

logger = logging.getLogger(__name__)


# =============================================================================
# WEBHOOK DATA STRUCTURE
# =============================================================================

class WebhookSubscription:
    """
    Webhook subscription data structure.

    Attributes:
        id: Unique subscription ID
        url: Webhook endpoint URL
        events: List of event patterns to subscribe to
        secret: HMAC secret for signature verification
        is_active: Whether subscription is active
        created_at: Creation timestamp
        last_delivery: Last delivery timestamp
        delivery_count: Number of deliveries
        failure_count: Number of consecutive failures
        headers: Custom headers to include
    """

    def __init__(self, id: str, url: str, events: List[str],
                 secret: str = None, is_active: bool = True,
                 headers: Optional[Dict[str, str]] = None,
                 created_at: datetime = None, last_delivery: datetime = None,
                 delivery_count: int = 0, failure_count: int = 0):
        self.id = id
        self.url = url
        self.events = events
        self.secret = secret or self._generate_secret()
        self.is_active = is_active
        self.headers = headers or {}
        self.created_at = created_at or datetime.utcnow()
        self.last_delivery = last_delivery
        self.delivery_count = delivery_count
        self.failure_count = failure_count

    def _generate_secret(self) -> str:
        """Generate a random webhook secret."""
        return uuid.uuid4().hex + uuid.uuid4().hex

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'url': self.url,
            'events': self.events,
            'secret': self.secret,
            'is_active': self.is_active,
            'headers': self.headers,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_delivery': self.last_delivery.isoformat() if self.last_delivery else None,
            'delivery_count': self.delivery_count,
            'failure_count': self.failure_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebhookSubscription':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            url=data['url'],
            events=data['events'],
            secret=data.get('secret'),
            is_active=data.get('is_active', True),
            headers=data.get('headers', {}),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            last_delivery=datetime.fromisoformat(data['last_delivery']) if data.get('last_delivery') else None,
            delivery_count=data.get('delivery_count', 0),
            failure_count=data.get('failure_count', 0)
        )


class WebhookDelivery:
    """
    Webhook delivery record.

    Attributes:
        id: Unique delivery ID
        subscription_id: ID of the subscription
        event_type: Event type that triggered delivery
        payload: Event payload sent
        status: Delivery status (pending, success, failed, retrying)
        response_status: HTTP response status code
        response_body: Response body (truncated)
        attempt_count: Number of delivery attempts
        next_retry: Next retry timestamp
        created_at: When delivery was created
        completed_at: When delivery completed
        error: Error message if failed
    """

    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_RETRYING = 'retrying'

    def __init__(self, id: str, subscription_id: str, event_type: str,
                 payload: Dict[str, Any], status: str = STATUS_PENDING,
                 response_status: int = None, response_body: str = None,
                 attempt_count: int = 0, next_retry: datetime = None,
                 created_at: datetime = None, completed_at: datetime = None,
                 error: str = None):
        self.id = id
        self.subscription_id = subscription_id
        self.event_type = event_type
        self.payload = payload
        self.status = status
        self.response_status = response_status
        self.response_body = response_body[:1000] if response_body else None  # Truncate
        self.attempt_count = attempt_count
        self.next_retry = next_retry
        self.created_at = created_at or datetime.utcnow()
        self.completed_at = completed_at
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'subscription_id': self.subscription_id,
            'event_type': self.event_type,
            'payload': self.payload,
            'status': self.status,
            'response_status': self.response_status,
            'response_body': self.response_body,
            'attempt_count': self.attempt_count,
            'next_retry': self.next_retry.isoformat() if self.next_retry else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error
        }


# =============================================================================
# WEBHOOK MANAGER
# =============================================================================

class WebhookManager:
    """
    Central webhook management system.

    Provides:
    - Subscription management
    - Event filtering and routing
    - Delivery with retry
    - Signature generation/verification
    - Delivery logging
    - Statistics and monitoring

    Usage:
        manager = WebhookManager()
        manager.subscribe(url='https://...', events=['domain.*'])
        manager.deliver('domain.invoice.created', {...})
    """

    def __init__(self):
        self._subscriptions: Dict[str, WebhookSubscription] = {}
        self._deliveries: Dict[str, WebhookDelivery] = {}
        self._delivery_queue = queue.Queue()
        self._worker_thread = None
        self._running = False

        # Retry configuration
        self.max_retries = 5
        self.retry_delays = [60, 300, 900, 3600, 10800]  # 1min, 5min, 15min, 1hr, 3hr
        self.timeout = 30  # seconds

    # =========================================================================
    # SUBSCRIPTION MANAGEMENT
    # =========================================================================

    def subscribe(self, url: str, events: List[str],
                 secret: Optional[str] = None,
                 headers: Optional[Dict[str, str]] = None,
                 subscription_id: Optional[str] = None) -> WebhookSubscription:
        """
        Subscribe to webhook events.

        Args:
            url: Webhook endpoint URL
            events: List of event patterns (supports * wildcard)
            secret: Optional HMAC secret for signature
            headers: Optional custom headers to include
            subscription_id: Optional custom ID

        Returns:
            The created WebhookSubscription
        """
        sub_id = subscription_id or str(uuid.uuid4())

        subscription = WebhookSubscription(
            id=sub_id,
            url=url,
            events=events,
            secret=secret,
            headers=headers
        )

        self._subscriptions[sub_id] = subscription
        logger.info(f"Created webhook subscription: {sub_id} -> {url}")

        self._persist_subscription(subscription)

        return subscription

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from webhook events.

        Args:
            subscription_id: ID of subscription to remove

        Returns:
            True if unsubscribed successfully
        """
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
            self._delete_subscription(subscription_id)
            logger.info(f"Unsubscribed webhook: {subscription_id}")
            return True
        return False

    def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get subscription by ID."""
        return self._subscriptions.get(subscription_id)

    def list_subscriptions(self, active_only: bool = False) -> List[WebhookSubscription]:
        """List all subscriptions."""
        subs = list(self._subscriptions.values())
        if active_only:
            subs = [s for s in subs if s.is_active]
        return subs

    def update_subscription(self, subscription_id: str,
                          updates: Dict[str, Any]) -> Optional[WebhookSubscription]:
        """
        Update subscription settings.

        Args:
            subscription_id: ID of subscription to update
            updates: Dict of fields to update

        Returns:
            Updated subscription or None
        """
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return None

        if 'url' in updates:
            subscription.url = updates['url']
        if 'events' in updates:
            subscription.events = updates['events']
        if 'secret' in updates:
            subscription.secret = updates['secret']
        if 'headers' in updates:
            subscription.headers = updates['headers']
        if 'is_active' in updates:
            subscription.is_active = updates['is_active']

        self._persist_subscription(subscription)
        return subscription

    # =========================================================================
    # DELIVERY
    # =========================================================================

    def deliver(self, event_type: str, payload: Dict[str, Any],
              sync: bool = False) -> List[WebhookDelivery]:
        """
        Deliver event to all matching subscriptions.

        Args:
            event_type: Event type (e.g., 'domain.invoice.created')
            payload: Event payload
            sync: If True, deliver synchronously; if False, async via queue

        Returns:
            List of delivery records
        """
        matching_subs = self._get_matching_subscriptions(event_type)

        if not matching_subs:
            logger.debug(f"No subscriptions match event: {event_type}")
            return []

        deliveries = []
        for sub in matching_subs:
            delivery = self._create_delivery(sub, event_type, payload)

            if sync:
                self._deliver_sync(delivery)
            else:
                self._delivery_queue.put(delivery)

            deliveries.append(delivery)

        # Start worker if not running
        if not sync and not self._running:
            self._start_worker()

        return deliveries

    def _get_matching_subscriptions(self, event_type: str) -> List[WebhookSubscription]:
        """Get subscriptions matching an event type."""
        matching = []

        for sub in self._subscriptions.values():
            if not sub.is_active:
                continue

            for pattern in sub.events:
                if self._matches_pattern(event_type, pattern):
                    matching.append(sub)
                    break

        return matching

    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches a pattern (supports * wildcard)."""
        if pattern == event_type:
            return True

        if pattern.endswith('.*'):
            prefix = pattern[:-2]
            if event_type.startswith(prefix + '.'):
                return True
            # Also match exact prefix
            if event_type == prefix:
                return True

        if pattern == '*':
            return True

        # Handle multi-level wildcards like domain.*
        if '.*' in pattern:
            prefix = pattern.split('.*')[0]
            if event_type.startswith(prefix + '.'):
                return True

        return False

    def _create_delivery(self, subscription: WebhookSubscription,
                       event_type: str, payload: Dict[str, Any]) -> WebhookDelivery:
        """Create a delivery record."""
        delivery = WebhookDelivery(
            id=str(uuid.uuid4()),
            subscription_id=subscription.id,
            event_type=event_type,
            payload=payload
        )
        self._deliveries[delivery.id] = delivery
        return delivery

    def _deliver_sync(self, delivery: WebhookDelivery) -> bool:
        """Deliver webhook synchronously."""
        subscription = self._subscriptions.get(delivery.subscription_id)
        if not subscription:
            delivery.status = WebhookDelivery.STATUS_FAILED
            delivery.error = 'Subscription not found'
            return False

        try:
            success, response = self._send_webhook(subscription, delivery)

            if success:
                delivery.status = WebhookDelivery.STATUS_SUCCESS
                delivery.response_status = response.get('status')
                delivery.response_body = response.get('body')
                delivery.completed_at = datetime.utcnow()
                subscription.last_delivery = datetime.utcnow()
                subscription.delivery_count += 1
                subscription.failure_count = 0
            else:
                self._handle_delivery_failure(delivery, subscription, response)

        except Exception as e:
            delivery.status = WebhookDelivery.STATUS_FAILED
            delivery.error = str(e)
            delivery.completed_at = datetime.utcnow()
            subscription.failure_count += 1
            logger.error(f"Webhook delivery error: {e}")

        self._persist_delivery(delivery)
        return delivery.status == WebhookDelivery.STATUS_SUCCESS

    def _handle_delivery_failure(self, delivery: WebhookDelivery,
                                subscription: WebhookSubscription,
                                response: Dict[str, Any]) -> None:
        """Handle failed delivery with retry logic."""
        delivery.attempt_count += 1

        if delivery.attempt_count >= self.max_retries:
            delivery.status = WebhookDelivery.STATUS_FAILED
            delivery.completed_at = datetime.utcnow()
            delivery.error = response.get('error', 'Max retries exceeded')
            subscription.failure_count += 1
            subscription.is_active = subscription.failure_count >= 10
            logger.warning(f"Webhook {subscription.id} deactivated after 10 failures")
        else:
            delivery.status = WebhookDelivery.STATUS_RETRYING
            delay_index = min(delivery.attempt_count - 1, len(self.retry_delays) - 1)
            delivery.next_retry = datetime.utcnow() + timedelta(seconds=self.retry_delays[delay_index])
            delivery.error = response.get('error', 'Delivery failed')
            logger.info(f"Webhook {subscription.id} retry scheduled in {self.retry_delays[delay_index]}s")

    def _send_webhook(self, subscription: WebhookSubscription,
                     delivery: WebhookDelivery) -> tuple:
        """
        Send webhook HTTP request.

        Args:
            subscription: Webhook subscription
            delivery: Delivery record

        Returns:
            Tuple of (success: bool, response: dict)
        """
        import urllib.request
        import urllib.error

        # Build payload
        payload = {
            'event': delivery.event_type,
            'timestamp': delivery.created_at.isoformat(),
            'delivery_id': delivery.id,
            'data': delivery.payload
        }

        payload_json = json.dumps(payload).encode('utf-8')

        # Build headers
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Event': delivery.event_type,
            'X-Webhook-Delivery-ID': delivery.id,
            'X-Webhook-Timestamp': delivery.created_at.isoformat()
        }

        # Add custom headers
        headers.update(subscription.headers or {})

        # Generate HMAC signature
        if subscription.secret:
            signature = self._generate_signature(payload_json, subscription.secret)
            headers['X-Webhook-Signature'] = f"sha256={signature}"

        # Send request
        req = urllib.request.Request(
            subscription.url,
            data=payload_json,
            headers=headers,
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = response.read().decode('utf-8')
                return True, {'status': response.status, 'body': body}

        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8') if e.fp else ''
            return False, {'status': e.code, 'error': f"HTTP {e.code}", 'body': body}

        except urllib.error.URLError as e:
            return False, {'error': str(e.reason)}

        except Exception as e:
            return False, {'error': str(e)}

    def _generate_signature(self, payload: bytes, secret: str) -> str:
        """Generate HMAC-SHA256 signature."""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        return signature

    def _verify_signature(self, payload: bytes, signature: str,
                        secret: str) -> bool:
        """Verify HMAC-SHA256 signature."""
        expected = self._generate_signature(payload, secret)
        return hmac.compare_digest(expected, signature)

    # =========================================================================
    # BACKGROUND WORKER
    # =========================================================================

    def _start_worker(self) -> None:
        """Start background delivery worker."""
        if self._worker_thread and self._worker_thread.is_alive():
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop)
        self._worker_thread.daemon = True
        self._worker_thread.start()
        logger.info("Webhook delivery worker started")

    def _worker_loop(self) -> None:
        """Background worker loop."""
        while self._running:
            try:
                # Check for due deliveries
                self._process_due_deliveries()

                # Process queue with timeout
                try:
                    delivery = self._delivery_queue.get(timeout=1.0)
                    self._deliver_sync(delivery)
                except queue.Empty:
                    pass

                # Check if we should stop
                if self._delivery_queue.empty() and not self._running:
                    break

            except Exception as e:
                logger.error(f"Webhook worker error: {e}")

    def _process_due_deliveries(self) -> None:
        """Process deliveries that are due for retry."""
        now = datetime.utcnow()

        for delivery in self._deliveries.values():
            if delivery.status == WebhookDelivery.STATUS_RETRYING:
                if delivery.next_retry and delivery.next_retry <= now:
                    self._deliver_sync(delivery)

    def _stop_worker(self) -> None:
        """Stop background worker."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
        logger.info("Webhook delivery worker stopped")

    # =========================================================================
    # PERSISTENCE (Stub - implement with database)
    # =========================================================================

    def _persist_subscription(self, subscription: WebhookSubscription) -> None:
        """Persist subscription to database."""
        # This is a stub - implement with actual database
        pass

    def _delete_subscription(self, subscription_id: str) -> None:
        """Delete subscription from database."""
        pass

    def _persist_delivery(self, delivery: WebhookDelivery) -> None:
        """Persist delivery record to database."""
        pass

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get webhook statistics."""
        total_subs = len(self._subscriptions)
        active_subs = sum(1 for s in self._subscriptions.values() if s.is_active)

        delivery_stats = {
            'pending': 0,
            'success': 0,
            'failed': 0,
            'retrying': 0
        }

        for d in self._deliveries.values():
            delivery_stats[d.status] = delivery_stats.get(d.status, 0) + 1

        return {
            'subscriptions': {
                'total': total_subs,
                'active': active_subs
            },
            'deliveries': delivery_stats,
            'queue_size': self._delivery_queue.qsize()
        }

    def get_delivery_history(self, subscription_id: str = None,
                           status: str = None,
                           limit: int = 100) -> List[WebhookDelivery]:
        """Get delivery history with filters."""
        deliveries = list(self._deliveries.values())

        if subscription_id:
            deliveries = [d for d in deliveries if d.subscription_id == subscription_id]
        if status:
            deliveries = [d for d in deliveries if d.status == status]

        deliveries.sort(key=lambda d: d.created_at, reverse=True)
        return deliveries[:limit]


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_webhook_manager = None

def get_webhook_manager() -> WebhookManager:
    """Get singleton webhook manager instance."""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def subscribe_webhook(url: str, events: List[str],
                    secret: str = None) -> WebhookSubscription:
    """
    Subscribe to webhook events.

    Usage:
        subscribe_webhook('https://example.com/hook', ['domain.invoice.*'])
    """
    return get_webhook_manager().subscribe(url=url, events=events, secret=secret)


def unsubscribe_webhook(subscription_id: str) -> bool:
    """Unsubscribe from webhook events."""
    return get_webhook_manager().unsubscribe(subscription_id)


def deliver_webhook(event_type: str, payload: Dict[str, Any],
                   sync: bool = False) -> List[WebhookDelivery]:
    """
    Deliver event to all matching subscriptions.

    Usage:
        deliver_webhook('domain.invoice.created', {'id': 123})
    """
    return get_webhook_manager().deliver(event_type, payload, sync)


def list_webhook_subscriptions(active_only: bool = False) -> List[WebhookSubscription]:
    """List all webhook subscriptions."""
    return get_webhook_manager().list_subscriptions(active_only)


# =============================================================================
# EVENT INTEGRATION
# =============================================================================

def setup_event_webhooks():
    """
    Set up webhooks to integrate with the event system.

    This connects the webhook manager to the event system so that
    events are automatically delivered to webhook subscribers.

    Call this during app initialization.
    """
    from event_system import EventBus, event_handler

    manager = get_webhook_manager()

    @event_handler('domain.*')
    def handle_domain_event(event):
        """Deliver domain events to webhooks."""
        manager.deliver(event.event_type, event.data)

    @event_handler('integration.*')
    def handle_integration_event(event):
        """Deliver integration events to webhooks."""
        manager.deliver(event.event_type, event.data)

    logger.info("Event webhook integration enabled")
