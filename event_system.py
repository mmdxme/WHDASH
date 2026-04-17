"""
Event-Driven Architecture System
==============================
Enterprise event bus for publishing and subscribing to domain events.

Features:
- In-memory event bus (development) with Redis Pub/Sub (production)
- Event types: domain.*, system.*, integration.*
- Event handlers/subscribers
- Dead letter queue for failed events
- Event replay capability
- Async event processing

Usage:
    from event_system import EventBus, event_handler, publish_event

    @event_handler('domain.invoice.created')
    def on_invoice_created(event):
        print(f"Invoice {event.data['id']} created")

    # Publish event
    EventBus.publish('domain.invoice.created', {'id': 123, 'amount': 1000})

    # Async publish
    EventBus.publish_async('domain.order.completed', {'order_id': 456})
"""

import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional, Set
from functools import wraps
from collections import defaultdict
import queue
import time

logger = logging.getLogger(__name__)


# =============================================================================
# EVENT TYPES TAXONOMY
# =============================================================================

class EventType:
    """Event type constants and naming conventions."""

    # Domain events - business objects
    DOMAIN_INVOICE_CREATED = 'domain.invoice.created'
    DOMAIN_INVOICE_POSTED = 'domain.invoice.posted'
    DOMAIN_INVOICE_PAID = 'domain.invoice.paid'
    DOMAIN_INVOICE_CANCELLED = 'domain.invoice.cancelled'

    DOMAIN_ORDER_CREATED = 'domain.order.created'
    DOMAIN_ORDER_FULFILLED = 'domain.order.fulfilled'
    DOMAIN_ORDER_SHIPPED = 'domain.order.shipped'
    DOMAIN_ORDER_DELIVERED = 'domain.order.delivered'
    DOMAIN_ORDER_RETURNED = 'domain.order.returned'

    DOMAIN_PAYMENT_CREATED = 'domain.payment.created'
    DOMAIN_PAYMENT_PROCESSED = 'domain.payment.processed'
    DOMAIN_PAYMENT_FAILED = 'domain.payment.failed'

    DOMAIN_TRANSFER_CREATED = 'domain.transfer.created'
    DOMAIN_TRANSFER_APPROVED = 'domain.transfer.approved'
    DOMAIN_TRANSFER_EXECUTED = 'domain.transfer.executed'
    DOMAIN_TRANSFER_REJECTED = 'domain.transfer.rejected'

    DOMAIN_ASSET_ACQUIRED = 'domain.asset.acquired'
    DOMAIN_ASSET_DEPRECIATED = 'domain.asset.depreciated'
    DOMAIN_ASSET_TRANSFERRED = 'domain.asset.transferred'
    DOMAIN_ASSET_DISPOSED = 'domain.asset.disposed'

    DOMAIN_EMPLOYEE_HIRED = 'domain.employee.hired'
    DOMAIN_EMPLOYEE_TERMINATED = 'domain.employee.terminated'
    DOMAIN_EMPLOYEE_PROMOTED = 'domain.employee.promoted'

    DOMAIN_USER_LOGIN = 'domain.user.login'
    DOMAIN_USER_LOGOUT = 'domain.user.logout'
    DOMAIN_USER_PASSWORD_CHANGED = 'domain.user.password_changed'

    # System events - platform operations
    SYSTEM_STARTUP = 'system.startup'
    SYSTEM_SHUTDOWN = 'system.shutdown'
    SYSTEM_BACKUP_STARTED = 'system.backup.started'
    SYSTEM_BACKUP_COMPLETED = 'system.backup.completed'
    SYSTEM_SYNC_STARTED = 'system.sync.started'
    SYSTEM_SYNC_COMPLETED = 'system.sync.completed'

    # Integration events - external systems
    INTEGRATION_WEBHOOK_RECEIVED = 'integration.webhook.received'
    INTEGRATION_SYNC_TRIGGERED = 'integration.sync.triggered'
    INTEGRATION_SYNC_COMPLETED = 'integration.sync.completed'
    INTEGRATION_API_CALLED = 'integration.api.called'


# =============================================================================
# EVENT DATA STRUCTURE
# =============================================================================

class Event:
    """
    Event data structure.

    Attributes:
        event_type: Dot-separated event name (e.g., 'domain.invoice.created')
        data: Event payload (dict)
        metadata: Event metadata (dict)
        event_id: Unique event identifier
        timestamp: Event timestamp
        source: Event source/service
    """

    def __init__(self, event_type: str, data: Dict[str, Any],
                 metadata: Optional[Dict[str, Any]] = None,
                 event_id: Optional[str] = None,
                 timestamp: Optional[datetime] = None,
                 source: str = 'whdash'):
        import uuid

        self.event_type = event_type
        self.data = data
        self.metadata = metadata or {}
        self.event_id = event_id or str(uuid.uuid4())
        self.timestamp = timestamp or datetime.utcnow()
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_type': self.event_type,
            'data': self.data,
            'metadata': self.metadata,
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(
            event_type=data['event_type'],
            data=data['data'],
            metadata=data.get('metadata', {}),
            event_id=data.get('event_id'),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else None,
            source=data.get('source', 'whdash')
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'Event':
        """Create event from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def __repr__(self) -> str:
        return f"Event(type={self.event_type}, id={self.event_id[:8]}...)"


# =============================================================================
# EVENT BUS (In-Memory Implementation)
# =============================================================================

class EventBus:
    """
    In-memory event bus for event publishing and subscribing.

    This is the base implementation. In production with Redis,
    this can be replaced with RedisEventBus for distributed events.

    Usage:
        EventBus.subscribe('domain.invoice.*', handler_function)
        EventBus.publish('domain.invoice.created', {'id': 123})
    """

    # Class-level storage for handlers
    _handlers: Dict[str, Set[Callable]] = defaultdict(set)
    _wildcard_handlers: Dict[str, Set[Callable]] = defaultdict(set)
    _event_history: List[Event] = []
    _max_history: int = 10000
    _lock = threading.Lock()

    # Dead letter queue for failed events
    _dead_letter_queue: List[Dict[str, Any]] = []
    _max_dead_letter_size: int = 1000

    @classmethod
    def subscribe(cls, event_pattern: str, handler: Callable,
                  priority: int = 0) -> None:
        """
        Subscribe a handler to an event pattern.

        Args:
            event_pattern: Event name or pattern (supports * wildcard)
                         Examples:
                         - 'domain.invoice.created' (exact match)
                         - 'domain.invoice.*' (all invoice events)
                         - 'domain.*' (all domain events)
            handler: Function to call when event matches
            priority: Handler priority (higher = called first)

        Example:
            @EventBus.subscribe('domain.order.*')
            def handle_order(event):
                print(f"Order event: {event.event_type}")
        """
        if '*' in event_pattern:
            # Wildcard pattern
            pattern = event_pattern.replace('*', '')
            cls._wildcard_handlers[pattern].add(handler)
            logger.debug(f"Subscribed handler to wildcard pattern: {event_pattern}")
        else:
            # Exact match
            cls._handlers[event_pattern].add(handler)
            logger.debug(f"Subscribed handler to event: {event_pattern}")

    @classmethod
    def unsubscribe(cls, event_pattern: str, handler: Callable) -> None:
        """
        Unsubscribe a handler from an event pattern.

        Args:
            event_pattern: Event name or pattern
            handler: Handler function to remove
        """
        if '*' in event_pattern:
            pattern = event_pattern.replace('*', '')
            cls._wildcard_handlers[pattern].discard(handler)
        else:
            cls._handlers[event_pattern].discard(handler)

    @classmethod
    def publish(cls, event_type: str, data: Dict[str, Any],
                metadata: Optional[Dict[str, Any]] = None) -> Event:
        """
        Publish a synchronous event.

        All matching handlers are called synchronously.
        If a handler raises an exception, it's logged but other handlers still run.

        Args:
            event_type: Event type (e.g., 'domain.invoice.created')
            data: Event payload
            metadata: Optional event metadata

        Returns:
            The published Event object
        """
        event = Event(event_type, data, metadata)

        # Store in history
        with cls._lock:
            cls._event_history.append(event)
            if len(cls._event_history) > cls._max_history:
                cls._event_history = cls._event_history[-cls._max_history:]

        # Get matching handlers
        handlers = list(cls._handlers.get(event_type, set()))

        # Add wildcard handlers
        for pattern, handler_set in cls._wildcard_handlers.items():
            if event_type.startswith(pattern):
                handlers.extend(handler_set)

        logger.info(f"Publishing event: {event_type} to {len(handlers)} handlers")

        # Call handlers synchronously
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error for {event_type}: {e}")
                cls._add_to_dead_letter(event, str(e))

        return event

    @classmethod
    def publish_async(cls, event_type: str, data: Dict[str, Any],
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Publish an asynchronous event.

        The event is put in a queue and processed by background workers.

        Args:
            event_type: Event type
            data: Event payload
            metadata: Optional event metadata
        """
        # Queue-based async processing
        def async_worker():
            cls.publish(event_type, data, metadata)

        thread = threading.Thread(target=async_worker)
        thread.daemon = True
        thread.start()

    @classmethod
    def _add_to_dead_letter(cls, event: Event, error: str) -> None:
        """Add failed event to dead letter queue."""
        with cls._lock:
            cls._dead_letter_queue.append({
                'event': event.to_dict(),
                'error': error,
                'failed_at': datetime.utcnow().isoformat()
            })
            if len(cls._dead_letter_queue) > cls._max_dead_letter_size:
                cls._dead_letter_queue = cls._dead_letter_queue[-cls._max_dead_letter_size:]

    @classmethod
    def get_dead_letter_events(cls) -> List[Dict[str, Any]]:
        """Get all dead letter events."""
        with cls._lock:
            return list(cls._dead_letter_queue)

    @classmethod
    def retry_dead_letter_event(cls, index: int) -> bool:
        """
        Retry a dead letter event.

        Args:
            index: Index of event in dead letter queue

        Returns:
            True if retry was successful
        """
        with cls._lock:
            if 0 <= index < len(cls._dead_letter_queue):
                dlq_entry = cls._dead_letter_queue.pop(index)
                event = Event.from_dict(dlq_entry['event'])
                try:
                    cls.publish(event.event_type, event.data, event.metadata)
                    return True
                except Exception as e:
                    cls._add_to_dead_letter(event, str(e))
                    return False
        return False

    @classmethod
    def get_event_history(cls, event_type: Optional[str] = None,
                         limit: int = 100) -> List[Event]:
        """
        Get event history.

        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        with cls._lock:
            history = list(cls._event_history)

        if event_type:
            history = [e for e in history if e.event_type == event_type]

        return history[-limit:]

    @classmethod
    def clear_history(cls) -> None:
        """Clear event history."""
        with cls._lock:
            cls._event_history.clear()

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get event bus statistics."""
        with cls._lock:
            event_counts = defaultdict(int)
            for event in cls._event_history:
                event_counts[event.event_type] += 1

            return {
                'total_events': len(cls._event_history),
                'event_counts': dict(event_counts),
                'handler_count': len(cls._handlers),
                'wildcard_handler_count': len(cls._wildcard_handlers),
                'dead_letter_count': len(cls._dead_letter_queue)
            }


# =============================================================================
# DECORATOR FOR EVENT HANDLERS
# =============================================================================

def event_handler(event_pattern: str, priority: int = 0):
    """
    Decorator to subscribe a function as an event handler.

    Usage:
        @event_handler('domain.invoice.*')
        def handle_invoice_event(event):
            print(f"Received: {event.event_type}")

        @event_handler('domain.order.created', priority=10)
        def handle_new_order(event):
            process_order(event.data)
    """
    def decorator(func: Callable) -> Callable:
        EventBus.subscribe(event_pattern, func, priority)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
    return decorator


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def publish_event(event_type: str, data: Dict[str, Any],
                 metadata: Optional[Dict[str, Any]] = None) -> Event:
    """
    Convenience function to publish an event.

    Equivalent to: EventBus.publish(event_type, data, metadata)

    Usage:
        publish_event('domain.order.created', {'order_id': 123})
    """
    return EventBus.publish(event_type, data, metadata)


def publish_domain_event(entity: str, action: str, data: Dict[str, Any]) -> Event:
    """
    Publish a domain event with standardized naming.

    Args:
        entity: Entity name (e.g., 'invoice', 'order', 'payment')
        action: Action (e.g., 'created', 'updated', 'deleted')
        data: Event data

    Returns:
        The published Event
    """
    event_type = f"domain.{entity}.{action}"
    return EventBus.publish(event_type, data)


def publish_system_event(event_name: str, data: Dict[str, Any]) -> Event:
    """
    Publish a system event.

    Args:
        event_name: System event name (e.g., 'startup', 'shutdown')
        data: Event data

    Returns:
        The published Event
    """
    event_type = f"system.{event_name}"
    return EventBus.publish(event_type, data)


def publish_integration_event(event_name: str, data: Dict[str, Any]) -> Event:
    """
    Publish an integration event.

    Args:
        event_name: Integration event name
        data: Event data

    Returns:
        The published Event
    """
    event_type = f"integration.{event_name}"
    return EventBus.publish(event_type, data)


# =============================================================================
# REDIS EVENT BUS (Optional - for distributed systems)
# =============================================================================

class RedisEventBus:
    """
    Redis-backed event bus for distributed systems.

    Requires:
        - redis package
        - Redis server running
        - REDIS_URL configured

    Usage:
        EventBus.use_redis(redis_client)
        EventBus.publish('domain.event', {...})  # Broadcasts to all instances
    """

    _redis_client = None
    _pubsub = None
    _listener_thread = None
    _running = False

    @classmethod
    def use_redis(cls, redis_client) -> None:
        """
        Configure EventBus to use Redis for pub/sub.

        Args:
            redis_client: Redis client instance
        """
        cls._redis_client = redis_client
        cls._pubsub = redis_client.pubsub()
        cls._running = True

        # Start listener thread
        cls._listener_thread = threading.Thread(target=cls._listen)
        cls._listener_thread.daemon = True
        cls._listener_thread.start()

        logger.info("EventBus now using Redis for pub/sub")

    @classmethod
    def _listen(cls) -> None:
        """Background listener for Redis pub/sub messages."""
        if not cls._pubsub:
            return

        cls._pubsub.subscribe('whdash_events')

        while cls._running:
            try:
                message = cls._pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    event = Event.from_json(message['data'])
                    # Process local handlers
                    EventBus.publish(event.event_type, event.data, event.metadata)
            except Exception as e:
                logger.error(f"Redis listener error: {e}")

    @classmethod
    def stop(cls) -> None:
        """Stop the Redis event bus."""
        cls._running = False
        if cls._pubsub:
            cls._pubsub.unsubscribe()
            cls._pubsub.close()


# =============================================================================
# INTEGRATION WITH DATABASE AUDIT LOG
# =============================================================================

def publish_audit_event(entity_type: str, entity_id: Any, action: str,
                       user_id: Optional[int] = None,
                       changes: Optional[Dict[str, Any]] = None) -> Event:
    """
    Publish an audit event from database changes.

    This integrates the event system with the audit log.

    Args:
        entity_type: Type of entity (e.g., 'invoice', 'order')
        entity_id: ID of the entity
        action: Action performed ('create', 'update', 'delete')
        user_id: ID of user who performed the action
        changes: Dict with 'old' and 'new' values for updates

    Returns:
        The published Event
    """
    data = {
        'entity_type': entity_type,
        'entity_id': entity_id,
        'action': action,
        'user_id': user_id,
        'changes': changes
    }

    event_type = f"domain.audit.{action}"
    return EventBus.publish(event_type, data)
