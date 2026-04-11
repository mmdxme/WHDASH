// Service Worker for MMDx Browser Notifications
const CACHE_NAME = 'whdash-notify-v1';

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
});

self.addEventListener('push', (event) => {
    if (!event.data) return;

    let data;
    try {
        data = event.data.json();
    } catch (e) {
        data = { title: 'MMDx Reminder', body: event.data.text() };
    }

    const title = data.title || 'MMDx Reminder';
    const options = {
        body: data.body || '',
        icon: data.icon || '/static/icon-notify.png',
        badge: data.badge || '/static/badge.png',
        tag: data.tag || 'whdash-notification',
        data: {
            url: data.url || '/email',
            emailId: data.emailId || null,
            accountId: data.accountId || null
        },
        requireInteraction: data.requireInteraction !== false,
        actions: [
            { action: 'open', title: 'View Email' },
            { action: 'dismiss', title: 'Dismiss' }
        ],
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

self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'dismiss') return;

    const url = event.notification.data && event.notification.data.url
        ? event.notification.data.url
        : '/email';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            // First try to find an existing window
            for (const client of clientList) {
                if (client.url.includes('/email') && 'focus' in client) {
                    client.focus();
                    client.postMessage({
                        type: 'NOTIFICATION_CLICK',
                        notification: event.notification.data
                    });
                    return;
                }
            }
            // If no existing window, open a new one
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});

self.addEventListener('message', (event) => {
    if (event.data) {
        if (event.data.type === 'SKIP_WAITING') {
            self.skipWaiting();
        }
        // Handle show notification request from main app
        if (event.data.type === 'SHOW_NOTIFICATION') {
            const data = event.data.payload;
            const title = data.title || 'New Email';
            const options = {
                body: data.body || '',
                icon: data.icon || '/static/icon-notify.png',
                badge: data.badge || '/static/badge.png',
                tag: 'email-' + (data.tag || Date.now()),
                data: {
                    url: data.url || '/email',
                    emailId: data.emailId || null,
                    accountId: data.accountId || null
                },
                requireInteraction: true,
                silent: data.silent || false,
                vibrate: data.silent ? [] : [200, 100, 200]
            };

            self.registration.showNotification(title, options);
        }
    }
});