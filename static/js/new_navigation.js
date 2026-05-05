/**
 * New Navigation System v2
 * Modern menu with search, favorites, drag-drop reordering, and hide/show
 */

class NewNavigation {
    constructor(options = {}) {
        this.storageKey = options.storageKey || 'navigation_prefs_v2';
        this.searchInputId = options.searchInputId || 'nav-search-input';
        this.menuContainerId = options.menuContainerId || 'new-sidebar-menu';
        this.apiBase = options.apiBase || '/api/navigation';
        this.debounceMs = options.debounceMs || 200;

        this.state = this.loadState();
        this.isDragging = false;
        this.draggedEl = null;
        this.dropIndicator = null;
        this.searchTimer = null;

        this.init();
    }

    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.bindAll());
        } else {
            this.bindAll();
        }
    }

    bindAll() {
        this.bindSearch();
        this.bindStarButtons();
        this.bindHideButtons();
        this.bindSectionToggles();
        this.bindResetButton();
        this.bindDragDrop();
        this.restoreState();
        this.updateFavoritesList();
        this.bindSubmenuLinks();
    }

    // ── State Management ──
    loadState() {
        try {
            const raw = localStorage.getItem(this.storageKey);
            if (raw) return JSON.parse(raw);
        } catch (e) {
            console.warn('[Nav] Load failed:', e);
        }
        return {
            favorites: [],
            order: {},
            hidden: [],
            expanded: {}
        };
    }

    saveState() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.state));
        } catch (e) {
            console.warn('[Nav] Save failed:', e);
        }
        this.syncToServer();
    }

    syncToServer() {
        const userId = window.currentUserId;
        if (!userId) return;
        const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
        fetch(`${this.apiBase}/prefs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
            body: JSON.stringify({
                user_id: userId,
                favorites: this.state.favorites,
                order: this.state.order,
                hidden: this.state.hidden,
                expanded: this.state.expanded
            })
        }).catch(() => {});
    }

    restoreState() {
        this.applyHidden();
        this.applyFavorites();
        this.applyOrder();
        this.applyExpanded();
    }

    // ── Search ──
    bindSearch() {
        const input = document.getElementById(this.searchInputId);
        if (!input) return;

        input.addEventListener('input', (e) => {
            clearTimeout(this.searchTimer);
            const q = e.target.value.trim().toLowerCase();

            const clearBtn = document.getElementById('nav-search-clear');
            if (clearBtn) clearBtn.classList.toggle('visible', q.length > 0);

            this.searchTimer = setTimeout(() => this.runSearch(q), this.debounceMs);
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                input.value = '';
                this.runSearch('');
                const clearBtn = document.getElementById('nav-search-clear');
                if (clearBtn) clearBtn.classList.remove('visible');
            }
        });
    }

    runSearch(query) {
        const sections = document.querySelectorAll('.nav-section');
        const emptyState = document.getElementById('nav-search-empty');

        if (!query) {
            sections.forEach(s => s.classList.remove('nav-search-hidden'));
            document.querySelectorAll('.nav-submenu-link').forEach(l => {
                l.classList.remove('nav-search-match');
            });
            if (emptyState) emptyState.classList.add('hidden');
            return;
        }

        let matches = 0;
        sections.forEach(section => {
            const label = section.querySelector('.nav-section-label')?.textContent?.toLowerCase() || '';
            const links = section.querySelectorAll('.nav-submenu-link');
            let hasMatch = label.includes(query);

            links.forEach(link => {
                const linkText = link.textContent?.toLowerCase() || '';
                if (linkText.includes(query)) {
                    hasMatch = true;
                    matches++;
                    link.classList.add('nav-search-match');
                    this.highlightMatch(link, query);
                } else {
                    link.classList.remove('nav-search-match');
                    this.unhighlightMatch(link);
                }
            });

            section.classList.toggle('nav-search-hidden', !hasMatch);
        });

        if (emptyState) emptyState.classList.toggle('hidden', matches > 0);
    }

    highlightMatch(el, query) {
        const span = el.querySelector('span');
        if (!span || span.dataset.original === undefined) {
            const original = span?.textContent || el.textContent;
            if (span) {
                span.dataset.original = original;
                const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
                span.innerHTML = original.replace(regex, '<mark class="nav-search-mark">$1</mark>');
            }
        }
    }

    unhighlightMatch(el) {
        const span = el.querySelector('span');
        if (span?.dataset.original !== undefined) {
            span.textContent = span.dataset.original;
            delete span.dataset.original;
        }
    }

    escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // ── Star/Favorites ──
    bindStarButtons() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-nav-star]');
            if (!btn) return;
            e.preventDefault();
            e.stopPropagation();
            const key = btn.dataset.navStar;
            const isFav = this.state.favorites.includes(key);
            if (isFav) {
                this.state.favorites = this.state.favorites.filter(f => f !== key);
            } else {
                this.state.favorites.push(key);
            }
            this.saveState();
            this.applyFavorites();
            this.updateFavoritesList();
        });
    }

    applyFavorites() {
        document.querySelectorAll('[data-nav-star]').forEach(btn => {
            const key = btn.dataset.navStar;
            const isFav = this.state.favorites.includes(key);
            const icon = btn.querySelector('i');
            btn.classList.toggle('active', isFav);
            if (icon) {
                icon.classList.toggle('fa-star', isFav);
                icon.classList.toggle('fa-star-o', !isFav);
                icon.classList.toggle('fas', isFav);
                icon.classList.toggle('far', !isFav);
            }
        });
    }

    updateFavoritesList() {
        const container = document.getElementById('nav-favorites-list');
        if (!container) return;

        if (this.state.favorites.length === 0) {
            const t = window.navTranslations || {};
            container.innerHTML = `
                <div class="nav-empty-state">
                    <i class="fa-solid fa-star text-lg mb-2 opacity-40"></i>
                    <p class="text-xs text-theme-muted">${t.no_favorites || 'No favorites yet'}</p>
                    <span class="text-xs opacity-60">${t.star_hint || 'Star menus to add them here'}</span>
                </div>
            `;
            return;
        }

        const html = this.state.favorites.map(key => {
            const link = document.querySelector(`[data-nav-item="${key}"]`) ||
                document.querySelector(`[data-nav-section="${key}"] .nav-section-toggle`);
            if (!link) return '';

            const label = link.querySelector('.nav-section-label')?.textContent ||
                          link.querySelector('span')?.textContent || key;
            const href = link.getAttribute('href') || '#';
            const iconEl = link.querySelector('i');
            const iconClass = iconEl ? iconEl.className : 'fa-star';

            return `
                <div class="nav-fav-item">
                    <a href="${href}" class="nav-fav-link">
                        <i class="${iconClass}"></i>
                        <span>${label.trim()}</span>
                    </a>
                    <button class="nav-fav-remove" data-remove-fav="${key}" title="Remove">
                        <i class="fa-solid fa-times"></i>
                    </button>
                </div>
            `;
        }).join('');

        container.innerHTML = html;

        container.querySelectorAll('[data-remove-fav]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const key = btn.dataset.removeFav;
                this.state.favorites = this.state.favorites.filter(f => f !== key);
                this.saveState();
                this.applyFavorites();
                this.updateFavoritesList();
            });
        });
    }

    // ── Hide/Show ──
    bindHideButtons() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-nav-hide]');
            if (!btn) return;
            e.preventDefault();
            e.stopPropagation();
            const key = btn.dataset.navHide;
            this.toggleHidden(key);
        });
    }

    toggleHidden(key) {
        const idx = this.state.hidden.indexOf(key);
        if (idx >= 0) {
            this.state.hidden.splice(idx, 1);
        } else {
            this.state.hidden.push(key);
        }
        this.saveState();
        this.applyHidden();
    }

    applyHidden() {
        document.querySelectorAll('.nav-section[data-nav-section]').forEach(section => {
            const key = section.dataset.navSection;
            if (key === 'favorites' || key === 'dashboard') return;
            section.classList.toggle('nav-section-hidden', this.state.hidden.includes(key));
        });
    }

    // ── Section Toggles ──
    // NOTE: Section toggle is handled by inline script in sidebar_menu.html
    // to ensure it works even if this JS fails to load or has errors.
    // This method is intentionally empty to avoid double-firing events.
    bindSectionToggles() {
        // Empty - delegated to sidebar_menu.html inline script
    }

    applyExpanded() {
        document.querySelectorAll('.nav-section[data-nav-section]').forEach(section => {
            const key = section.dataset.navSection;
            const isOpen = this.state.expanded[key];
            if (isOpen !== undefined) {
                section.classList.toggle('is-open', isOpen);
            }
        });
    }

    // ── Submenu Active Links ──
    bindSubmenuLinks() {
        document.addEventListener('click', (e) => {
            const link = e.target.closest('.nav-submenu-link');
            if (!link) return;
            document.querySelectorAll('.nav-submenu-link').forEach(l => l.classList.remove('is-active'));
            link.classList.add('is-active');
        });
    }

    // ── Drag & Drop ──
    bindDragDrop() {
        document.addEventListener('dragstart', (e) => {
            const section = e.target.closest('.nav-section[data-nav-section]');
            if (!section) return;
            const key = section.dataset.navSection;
            if (key === 'favorites' || key === 'dashboard') return;
            this.isDragging = true;
            this.draggedEl = section;
            section.classList.add('nav-dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', key);
        });

        document.addEventListener('dragend', () => {
            this.isDragging = false;
            if (this.draggedEl) {
                this.draggedEl.classList.remove('nav-dragging');
                this.draggedEl = null;
            }
            document.querySelectorAll('.nav-drop-target').forEach(el => el.classList.remove('nav-drop-target'));
            if (this.dropIndicator) {
                this.dropIndicator.remove();
                this.dropIndicator = null;
            }
        });

        document.addEventListener('dragover', (e) => {
            if (!this.isDragging) return;
            e.preventDefault();
            const section = e.target.closest('.nav-section[data-nav-section]');
            if (!section || section === this.draggedEl) return;
            e.dataTransfer.dropEffect = 'move';
            section.classList.add('nav-drop-target');
            if (!this.dropIndicator) {
                this.dropIndicator = document.createElement('div');
                this.dropIndicator.className = 'nav-drop-indicator';
            }
            const rect = section.getBoundingClientRect();
            const midY = rect.top + rect.height / 2;
            if (e.clientY < midY) {
                section.parentElement.insertBefore(this.dropIndicator, section);
            } else {
                section.parentElement.insertBefore(this.dropIndicator, section.nextSibling);
            }
        });

        document.addEventListener('dragleave', (e) => {
            const section = e.target.closest('.nav-section');
            if (section) section.classList.remove('nav-drop-target');
        });

        document.addEventListener('drop', (e) => {
            if (!this.isDragging || !this.draggedEl) return;
            e.preventDefault();
            const target = e.target.closest('.nav-section[data-nav-section]');
            if (!target || target === this.draggedEl) return;

            const container = target.parentElement;
            const rect = target.getBoundingClientRect();
            const insertBefore = e.clientY < rect.top + rect.height / 2;

            if (insertBefore) {
                container.insertBefore(this.draggedEl, target);
            } else {
                container.insertBefore(this.draggedEl, target.nextSibling);
            }

            this.saveOrder();
            target.classList.remove('nav-drop-target');
        });
    }

    saveOrder() {
        const container = document.getElementById(this.menuContainerId);
        if (!container) return;
        const sections = container.querySelectorAll('.nav-section[data-nav-section]');
        sections.forEach((section, idx) => {
            const key = section.dataset.navSection;
            if (key && key !== 'favorites' && key !== 'dashboard') {
                this.state.order[key] = idx;
            }
        });
        this.saveState();
    }

    applyOrder() {
        const container = document.getElementById(this.menuContainerId);
        if (!container) return;
        const sections = Array.from(container.querySelectorAll('.nav-section[data-nav-section]'));
        sections.sort((a, b) => {
            const aKey = a.dataset.navSection;
            const bKey = b.dataset.navSection;
            const aOrder = this.state.order[aKey] ?? 999;
            const bOrder = this.state.order[bKey] ?? 999;
            return aOrder - bOrder;
        }).forEach(section => container.appendChild(section));
    }

    // ── Reset ──
    bindResetButton() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('#nav-reset-prefs');
            if (!btn) return;
            e.preventDefault();
            this.state = { favorites: [], order: {}, hidden: [], expanded: {} };
            this.saveState();
            document.querySelectorAll('.nav-section').forEach(s => {
                s.classList.remove('nav-section-hidden');
            });
            this.applyFavorites();
            this.updateFavoritesList();
            const input = document.getElementById(this.searchInputId);
            if (input) input.value = '';
            this.runSearch('');
        });
    }

    // ── Public: Search Handler ──
    handleSearch(query) {
        const input = document.getElementById(this.searchInputId);
        if (input) input.value = query;
        this.runSearch(query);
        const clearBtn = document.getElementById('nav-search-clear');
        if (clearBtn) clearBtn.classList.toggle('visible', query.length > 0);
    }
}

// Initialize globally
window.Navigation = new NewNavigation({
    storageKey: 'navigation_prefs_v2',
    searchInputId: 'nav-search-input',
    menuContainerId: 'new-sidebar-menu',
    apiBase: '/api/navigation'
});