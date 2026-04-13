// Service Worker for MMDx + FLOW Browser Notifications
const CACHE_NAME = 'whdash-notify-v2';

// Notification types
const NOTIFICATION_TYPES = {
    EMAIL: 'email',
    FLOW_MESSAGE: 'flow_message',
    FLOW_MENTION: 'flow_mention',
    FLOW_CALL: 'flow_call',
    FLOW_MEETING: 'flow_meeting',
    FLOW_REMINDER: 'flow_reminder',
    WORKFLOW: 'workflow',
    TASK: 'task',
    ISSUE: 'issue',
    SYSTEM: 'system'
};

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
});

// Handle push notifications
self.addEventListener('push', (event) => {
    if (!event.data) return;

    let data;
    try {
        data = event.data.json();
    } catch (e) {
        data = { title: 'New Notification', body: event.data.text() };
    }

    const notificationType = data.notification_type || NOTIFICATION_TYPES.SYSTEM;
    const title = data.title || 'MMDx';
    const icon = getIconForType(notificationType, data.icon);
    
    const options = {
        body: data.body || '',
        icon: icon,
        badge: '/static/badge.png',
        tag: data.tag || `whdash-${notificationType}-${Date.now()}`,
        data: {
            type: notificationType,
            url: data.url || '/',
            notificationId: data.notification_id || null,
            conversationId: data.conversation_id || null,
            messageId: data.message_id || null,
            timestamp: Date.now()
        },
        requireInteraction: shouldRequireInteraction(notificationType),
        actions: getActionsForType(notificationType, data.url),
        vibrate: [200, 100, 200],
        silent: data.silent || false
    };

    if (data.sound && !options.silent) {
        options.sound = data.sound;
    }

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'dismiss') return;

    const notificationData = event.notification.data || {};
    const url = notificationData.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            // Try to find existing window with same URL
            for (const client of clientList) {
                if (client.url.includes(url) && 'focus' in client) {
                    client.focus();
                    client.postMessage({
                        type: 'NOTIFICATION_CLICK',
                        notification: notificationData
                    });
                    return;
                }
            }
            // Open new window if not found
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});

// Handle messages from main app
self.addEventListener('message', (event) => {
    if (!event.data) return;

    const { type, payload } = event.data;

    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;

        case 'SHOW_NOTIFICATION':
            showNotification(payload);
            break;

        case 'SUBSCRIBE_PUSH':
            // Handle push subscription from main app
            handlePushSubscription(payload);
            break;

        case 'UNSUBSCRIBE_PUSH':
            handlePushUnsubscription(payload);
            break;

        case 'FLOW_MESSAGE':
            showFlowMessageNotification(payload);
            break;

        case 'FLOW_CALL':
            showFlowCallNotification(payload);
            break;

        default:
            console.log('Unknown message type:', type);
    }
});

// Show Flow message notification
function showFlowMessageNotification(data) {
    const options = {
        body: data.body || '',
        icon: data.senderAvatar || '/static/icon-notify.png',
        badge: '/static/badge.png',
        tag: `flow-message-${data.conversationId}-${Date.now()}`,
        data: {
            type: NOTIFICATION_TYPES.FLOW_MESSAGE,
            url: `/flow/chat/${data.conversationId}`,
            conversationId: data.conversationId,
            messageId: data.messageId,
            senderName: data.senderName,
            timestamp: Date.now()
        },
        requireInteraction: false,
        actions: [
            { action: 'reply', title: 'Reply' },
            { action: 'markread', title: 'Mark Read' },
            { action: 'dismiss', title: 'Dismiss' }
        ],
        vibrate: [200, 100, 200]
    };

    self.registration.showNotification(data.title || 'New Message', options);
}

// Show Flow call notification
function showFlowCallNotification(data) {
    const options = {
        body: data.body || 'Incoming call',
        icon: data.callerAvatar || '/static/icon-notify.png',
        badge: '/static/badge.png',
        tag: `flow-call-${data.callId}`,
        data: {
            type: NOTIFICATION_TYPES.FLOW_CALL,
            url: `/flow/call/${data.callId}`,
            callId: data.callId,
            callType: data.callType,
            callerName: data.callerName,
            timestamp: Date.now()
        },
        requireInteraction: true,
        actions: [
            { action: 'accept', title: 'Accept' },
            { action: 'decline', title: 'Decline' }
        ],
        vibrate: [300, 150, 300, 150, 300],
        silent: false
    };

    self.registration.showNotification(data.title || 'Incoming Call', options);
}

// Show generic notification
function showNotification(data) {
    const notificationType = data.notification_type || NOTIFICATION_TYPES.SYSTEM;
    
    const options = {
        body: data.body || '',
        icon: getIconForType(notificationType, data.icon),
        badge: '/static/badge.png',
        tag: data.tag || `whdash-${notificationType}-${Date.now()}`,
        data: {
            type: notificationType,
            url: data.url || '/',
            notificationId: data.notification_id || null,
            timestamp: Date.now()
        },
        requireInteraction: shouldRequireInteraction(notificationType),
        actions: getActionsForType(notificationType, data.url),
        vibrate: [200, 100, 200],
        silent: data.silent || false
    };

    self.registration.showNotification(data.title || 'Notification', options);
}

// Handle push subscription
async function handlePushSubscription(payload) {
    try {
        const subscription = await self.registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: payload.vapidPublicKey
        });
        
        // Send subscription to server
        const response = await fetch('/flow/api/push/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                subscription: subscription.toJSON(),
                user_id: payload.userId
            })
        });
        
        if (response.ok) {
            console.log('Push subscription successful');
        }
    } catch (error) {
        console.error('Push subscription failed:', error);
    }
}

// Handle push unsubscription
async function handlePushUnsubscription(payload) {
    try {
        const subscription = await self.registration.pushManager.getSubscription();
        if (subscription) {
            await subscription.unsubscribe();
            
            await fetch('/flow/api/push/unsubscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: payload.userId
                })
            });
        }
    } catch (error) {
        console.error('Push unsubscription failed:', error);
    }
}

// Helper: Get icon for notification type
function getIconForType(type, customIcon) {
    if (customIcon) return customIcon;
    
    const icons = {
        [NOTIFICATION_TYPES.FLOW_MESSAGE]: '/static/flow-icon.png',
        [NOTIFICATION_TYPES.FLOW_MENTION]: '/static/flow-mention.png',
        [NOTIFICATION_TYPES.FLOW_CALL]: '/static/flow-call.png',
        [NOTIFICATION_TYPES.FLOW_MEETING]: '/static/flow-meeting.png',
        [NOTIFICATION_TYPES.FLOW_REMINDER]: '/static/flow-reminder.png',
        [NOTIFICATION_TYPES.EMAIL]: '/static/icon-notify.png',
        [NOTIFICATION_TYPES.WORKFLOW]: '/static/icon-workflow.png',
        [NOTIFICATION_TYPES.TASK]: '/static/icon-task.png',
        [NOTIFICATION_TYPES.ISSUE]: '/static/icon-issue.png',
        [NOTIFICATION_TYPES.SYSTEM]: '/static/icon-notify.png'
    };
    
    return icons[type] || '/static/icon-notify.png';
}

// Helper: Determine if notification should require interaction
function shouldRequireInteraction(type) {
    const interactiveTypes = [
        NOTIFICATION_TYPES.FLOW_CALL,
        NOTIFICATION_TYPES.FLOW_MEETING,
        NOTIFICATION_TYPES.WORKFLOW,
        NOTIFICATION_TYPES.TASK,
        NOTIFICATION_TYPES.ISSUE
    ];
    return interactiveTypes.includes(type);
}

// Helper: Get actions for notification type
function getActionsForType(type, url) {
    const baseActions = [
        { action: 'open', title: 'Open' },
        { action: 'dismiss', title: 'Dismiss' }
    ];
    
    const typeActions = {
        [NOTIFICATION_TYPES.FLOW_MESSAGE]: [
            { action: 'reply', title: 'Reply' },
            { action: 'markread', title: 'Mark Read' },
            { action: 'dismiss', title: 'Dismiss' }
        ],
        [NOTIFICATION_TYPES.FLOW_CALL]: [
            { action: 'accept', title: 'Accept' },
            { action: 'decline', title: 'Decline' }
        ],
        [NOTIFICATION_TYPES.FLOW_MEETING]: [
            { action: 'join', title: 'Join Meeting' },
            { action: 'dismiss', title: 'Dismiss' }
        ],
        [NOTIFICATION_TYPES.FLOW_REMINDER]: [
            { action: 'snooze', title: 'Snooze' },
            { action: 'complete', title: 'Mark Complete' }
        ]
    };
    
    return typeActions[type] || baseActions;
}
