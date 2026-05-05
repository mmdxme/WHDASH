/**
 * Quick Tools Panel
 * ================
 * Floating quick-tools system with:
 * - Calculator (Basic + Scientific)
 * - Quick Notes (with search, sort, categories)
 * - Quick Task Creator
 * - Quick Issue Creator
 * - Personal Reminders (with repeat options, snooze)
 * - Quick Navigation / Favorites
 * - Usage Analytics Dashboard
 */

(function() {
    'use strict';

    // State
    let isPanelOpen = false;
    let currentTool = 'calculator';
    let calcExpression = '';
    let calcHistory = [];
    let calcScientificMode = false;

    // DOM Elements
    let panelEl = null;
    let fabEl = null;

    // Tool launcher state
    let recentTools = [];
    let favoriteTools = [];

    // Notes state
    let notesSearchQuery = '';
    let notesSortBy = 'updated';

    // Tasks state
    let tasksFilter = 'all';

    // Reminder snooze options
    const SNOOZE_OPTIONS = [
        { label: '5 min', minutes: 5 },
        { label: '10 min', minutes: 10 },
        { label: '15 min', minutes: 15 },
        { label: '30 min', minutes: 30 },
        { label: '1 hour', minutes: 60 }
    ];

    // Translations helper
    function t(key, fallback) {
        if (window.TRANSLATIONS && window.currentLang) {
            return window.TRANSLATIONS[window.currentLang][key] || fallback || key;
        }
        return fallback || key;
    }

    // CSRF Token helper for fetch requests
    function getCsrfHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': window.csrfToken || ''
        };
        return headers;
    }

    // Initialize
    function init() {
        // Get CSRF token from page if available
        const csrfInput = document.querySelector('meta[name="csrf-token"]');
        if (csrfInput) {
            window.csrfToken = csrfInput.content;
        }

        // Load recent tools from localStorage
        try {
            recentTools = JSON.parse(localStorage.getItem('qt_recent_tools') || '[]');
            favoriteTools = JSON.parse(localStorage.getItem('qt_favorite_tools') || '[]');
        } catch (e) {}

        createFAB();
        createPanel();
        bindEvents();
        loadPreferences();
        loadFavorites(); // Load favorites for sidebar
        checkDueReminders();
        loadUsageAnalytics();
    }

    // Create Floating Action Button
    function createFAB() {
        fabEl = document.createElement('div');
        fabEl.id = 'quick-tools-fab';
        fabEl.innerHTML = `
            <button id="quick-tools-btn" class="quick-fab-btn" aria-label="${t('open_tools', 'Open Quick Tools')}" title="${t('quick_tools', 'Quick Tools')}">
                <i class="fa-solid fa-flask"></i>
                <i class="fa-solid fa-xmark quick-fab-close"></i>
            </button>
            <div id="quick-tools-badge" class="quick-fab-badge" style="display:none;">0</div>
        `;
        document.body.appendChild(fabEl);
    }

    // Create Panel
    function createPanel() {
        panelEl = document.createElement('div');
        panelEl.id = 'quick-tools-panel';
        panelEl.className = 'quick-panel glass-panel';
        panelEl.setAttribute('role', 'dialog');
        panelEl.setAttribute('aria-label', t('quick_tools_panel', 'Quick Tools Panel'));
        panelEl.innerHTML = getPanelHTML();
        document.body.appendChild(panelEl);
    }

    function getPanelHTML() {
        return `
            <div class="quick-panel-header">
                <div class="quick-panel-tabs">
                    <button class="quick-tab" data-tool="launcher" title="${t('tools', 'Tools')}">
                        <i class="fa-solid fa-grip"></i>
                        <span>${t('tools', 'Tools')}</span>
                    </button>
                    <button class="quick-tab active" data-tool="calculator" title="${t('calculator', 'Calculator')}">
                        <i class="fa-solid fa-calculator"></i>
                        <span>${t('calculator', 'Calc')}</span>
                    </button>
                    <button class="quick-tab" data-tool="notes" title="${t('quick_notes', 'Notes')}">
                        <i class="fa-solid fa-note-sticky"></i>
                        <span>${t('notes', 'Notes')}</span>
                    </button>
                    <button class="quick-tab" data-tool="tasks" title="${t('quick_task', 'Tasks')}">
                        <i class="fa-solid fa-check-circle"></i>
                        <span>${t('tasks', 'Tasks')}</span>
                    </button>
                    <button class="quick-tab" data-tool="issues" title="${t('quick_issue', 'Issues')}">
                        <i class="fa-solid fa-bug"></i>
                        <span>${t('issues', 'Issues')}</span>
                    </button>
                    <button class="quick-tab" data-tool="reminders" title="${t('reminders', 'Reminders')}">
                        <i class="fa-solid fa-bell"></i>
                        <span>${t('reminders', 'Reminders')}</span>
                    </button>
                    <button class="quick-tab" data-tool="favorites" title="${t('favorites', 'Favorites')}">
                        <i class="fa-solid fa-star"></i>
                        <span>${t('favorites', 'Favorites')}</span>
                    </button>
                </div>
                <button class="quick-panel-close" aria-label="${t('close_tools', 'Close')}">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
            <div class="quick-panel-content">
                <!-- Tool Launcher -->
                <div id="quick-tool-launcher" class="quick-tool-content">
                    ${getLauncherHTML()}
                </div>
                <!-- Calculator Tool -->
                <div id="quick-tool-calculator" class="quick-tool-content active">
                    ${getCalculatorHTML()}
                </div>
                <!-- Notes Tool -->
                <div id="quick-tool-notes" class="quick-tool-content">
                    ${getNotesHTML()}
                </div>
                <!-- Tasks Tool -->
                <div id="quick-tool-tasks" class="quick-tool-content">
                    ${getTaskHTML()}
                </div>
                <!-- Issues Tool -->
                <div id="quick-tool-issues" class="quick-tool-content">
                    ${getIssueHTML()}
                </div>
                <!-- Reminders Tool -->
                <div id="quick-tool-reminders" class="quick-tool-content">
                    ${getRemindersHTML()}
                </div>
                <!-- Favorites Tool -->
                <div id="quick-tool-favorites" class="quick-tool-content">
                    ${getFavoritesHTML()}
                </div>
            </div>
        `;
    }

    function getLauncherHTML() {
        return `
            <div class="launcher-container">
                <div class="launcher-search">
                    <i class="fa-solid fa-search"></i>
                    <input type="text" id="launcher-search" placeholder="${t('search_tools', 'Search tools...')}" autocomplete="off">
                </div>
                <div class="launcher-grid">
                    ${getToolCards()}
                </div>
            </div>
        `;
    }

    function getToolCards() {
        const tools = [
            { id: 'calculator', icon: 'fa-calculator', label: t('calculator', 'Calculator'), desc: t('calc_desc', 'Basic & scientific calculations') },
            { id: 'notes', icon: 'fa-note-sticky', label: t('quick_notes', 'Notes'), desc: t('notes_desc', 'Quick notes & reminders') },
            { id: 'tasks', icon: 'fa-check-circle', label: t('quick_task', 'Tasks'), desc: t('tasks_desc', 'Create quick tasks') },
            { id: 'issues', icon: 'fa-bug', label: t('quick_issue', 'Issues'), desc: t('issues_desc', 'Report issues quickly') },
            { id: 'reminders', icon: 'fa-bell', label: t('reminders', 'Reminders'), desc: t('reminders_desc', 'Set reminders & alerts') },
            { id: 'favorites', icon: 'fa-star', label: t('favorites', 'Favorites'), desc: t('favorites_desc', 'Quick access links') },
            { id: 'analytics', icon: 'fa-chart-bar', label: t('analytics', 'Analytics'), desc: t('analytics_desc', 'Usage reports & stats') }
        ];

        return tools.map(tool => `
            <div class="tool-card" data-tool="${tool.id}">
                <div class="tool-card-icon">
                    <i class="fa-solid ${tool.icon}"></i>
                </div>
                <div class="tool-card-label">${tool.label}</div>
                <div class="tool-card-desc">${tool.desc}</div>
            </div>
        `).join('');
    }

    function getCalculatorHTML() {
        return `
            <div class="calc-display">
                <div class="calc-mode-toggle">
                    <button class="calc-mode-btn ${calcScientificMode ? '' : 'active'}" data-mode="basic">${t('basic', 'Basic')}</button>
                    <button class="calc-mode-btn ${calcScientificMode ? 'active' : ''}" data-mode="scientific">${t('scientific', 'Scientific')}</button>
                </div>
                <input type="text" id="calc-expression" class="calc-expression" value="" readonly placeholder="0">
                <div id="calc-result" class="calc-result"></div>
                ${calcHistory.length > 0 ? `
                <div class="calc-history-toggle">
                    <button id="calc-history-toggle" title="${t('calc_history', 'History')}">
                        <i class="fa-solid fa-clock-rotate-left"></i>
                    </button>
                </div>
                ` : ''}
            </div>
            <div class="calc-buttons">
                <button class="calc-btn calc-clear" data-action="clear">C</button>
                <button class="calc-btn calc-backspace" data-action="backspace">
                    <i class="fa-solid fa-delete-left"></i>
                </button>
                <button class="calc-btn calc-percent" data-action="%">%</button>
                <button class="calc-btn calc-op" data-op="/">/</button>
                <button class="calc-btn" data-num="7">7</button>
                <button class="calc-btn" data-num="8">8</button>
                <button class="calc-btn" data-num="9">9</button>
                <button class="calc-btn calc-op" data-op="*">&times;</button>
                <button class="calc-btn" data-num="4">4</button>
                <button class="calc-btn" data-num="5">5</button>
                <button class="calc-btn" data-num="6">6</button>
                <button class="calc-btn calc-op" data-op="-">-</button>
                <button class="calc-btn" data-num="1">1</button>
                <button class="calc-btn" data-num="2">2</button>
                <button class="calc-btn" data-num="3">3</button>
                <button class="calc-btn calc-op" data-op="+">+</button>
                <button class="calc-btn calc-zero" data-num="0">0</button>
                <button class="calc-btn" data-action=".">.</button>
                <button class="calc-btn calc-equals" data-action="=">=</button>
            </div>
            <div class="calc-scientific-buttons ${calcScientificMode ? 'active' : ''}">
                <button class="calc-btn calc-sci" data-sci="sin">sin</button>
                <button class="calc-btn calc-sci" data-sci="cos">cos</button>
                <button class="calc-btn calc-sci" data-sci="tan">tan</button>
                <button class="calc-btn calc-sci" data-sci="sqrt">&radic;</button>
                <button class="calc-btn calc-sci" data-sci="sq">x&sup2;</button>
                <button class="calc-btn calc-sci" data-sci="pow">x<sup>y</sup></button>
                <button class="calc-btn calc-sci" data-sci="pi">&pi;</button>
                <button class="calc-btn calc-sci" data-sci="e">e</button>
            </div>
            <div class="calc-history-panel ${calcHistory.length > 0 ? 'active' : ''}" id="calc-history-panel">
                <div class="calc-history-header">
                    <span>${t('history', 'History')}</span>
                    <button id="calc-history-clear">${t('clear', 'Clear')}</button>
                </div>
                <div class="calc-history-list" id="calc-history-list">
                    ${calcHistory.slice(-10).reverse().map(h => `
                        <div class="calc-history-item" data-expr="${escapeHtml(h.expression)}">
                            <span class="hist-expr">${escapeHtml(h.expression)}</span>
                            <span class="hist-result">= ${h.result}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            <div class="calc-actions">
                <button class="calc-copy-btn" id="calc-copy" title="${t('copy_result', 'Copy Result')}">
                    <i class="fa-regular fa-copy"></i> ${t('copy_result', 'Copy')}
                </button>
            </div>
        `;
    }

    function getNotesHTML() {
        return `
            <div class="notes-container">
                <div class="notes-toolbar">
                    <div class="notes-search">
                        <i class="fa-solid fa-search"></i>
                        <input type="text" id="notes-search" placeholder="${t('search_notes', 'Search notes...')}" value="${escapeHtml(notesSearchQuery)}">
                    </div>
                    <div class="notes-sort">
                        <select id="notes-sort">
                            <option value="updated" ${notesSortBy === 'updated' ? 'selected' : ''}>${t('sort_updated', 'Last Updated')}</option>
                            <option value="created" ${notesSortBy === 'created' ? 'selected' : ''}>${t('sort_created', 'Created')}</option>
                            <option value="alpha" ${notesSortBy === 'alpha' ? 'selected' : ''}>${t('sort_alpha', 'A-Z')}</option>
                        </select>
                    </div>
                </div>
                <div class="notes-input-area">
                    <input type="text" id="note-title" class="note-title-input" placeholder="${t('quick_note', 'Note title...')}">
                    <textarea id="note-content" class="note-content-input" placeholder="${t('note_placeholder', 'Write your note here...')}"></textarea>
                    <div class="notes-color-picker">
                        <button class="color-btn active" data-color="blue" style="background:#3b82f6;"></button>
                        <button class="color-btn" data-color="green" style="background:#22c55e;"></button>
                        <button class="color-btn" data-color="yellow" style="background:#eab308;"></button>
                        <button class="color-btn" data-color="red" style="background:#ef4444;"></button>
                        <button class="color-btn" data-color="purple" style="background:#a855f7;"></button>
                        <button class="color-btn" data-color="gray" style="background:#6b7280;"></button>
                    </div>
                    <button class="notes-add-btn" id="note-add">
                        <i class="fa-solid fa-plus"></i> ${t('add_note', 'Add Note')}
                    </button>
                </div>
                <div class="notes-list" id="notes-list">
                    <div class="notes-empty">
                        <i class="fa-solid fa-note-sticky"></i>
                        <p>${t('no_notes', 'No notes yet')}</p>
                        <span>${t('no_notes_desc', 'Create a note to get started')}</span>
                    </div>
                </div>
            </div>
        `;
    }

    function getTaskHTML() {
        return `
            <div class="task-form-container">
                <div class="task-filters">
                    <button class="task-filter-btn ${tasksFilter === 'all' ? 'active' : ''}" data-filter="all">${t('all', 'All')}</button>
                    <button class="task-filter-btn ${tasksFilter === 'today' ? 'active' : ''}" data-filter="today">${t('today', 'Today')}</button>
                    <button class="task-filter-btn ${tasksFilter === 'overdue' ? 'active' : ''}" data-filter="overdue">${t('overdue', 'Overdue')}</button>
                    <button class="task-filter-btn ${tasksFilter === 'completed' ? 'active' : ''}" data-filter="completed">${t('completed', 'Completed')}</button>
                </div>
                <div class="task-form">
                    <div class="form-group">
                        <label>${t('task_title', 'Title')}</label>
                        <input type="text" id="task-title" placeholder="${t('quick_task', 'Task title...')}" maxlength="200">
                    </div>
                    <div class="form-group">
                        <label>${t('task_description', 'Description')}</label>
                        <textarea id="task-description" placeholder="${t('task_description', 'Description...')}" rows="2"></textarea>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>${t('task_priority', 'Priority')}</label>
                            <select id="task-priority">
                                <option value="Low">${t('priority_low', 'Low')}</option>
                                <option value="Medium" selected>${t('priority_medium', 'Medium')}</option>
                                <option value="High">${t('priority_high', 'High')}</option>
                                <option value="Critical">${t('priority_critical', 'Critical')}</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>${t('task_due_date', 'Due Date')}</label>
                            <input type="datetime-local" id="task-due-date">
                        </div>
                    </div>
                    <button class="task-create-btn" id="task-create">
                        <i class="fa-solid fa-plus"></i> ${t('create_task', 'Create Task')}
                    </button>
                </div>
            </div>
        `;
    }

    function getIssueHTML() {
        return `
            <div class="issue-form-container">
                <div class="issue-form">
                    <div class="form-group">
                        <label>${t('issue_title', 'Title')}</label>
                        <input type="text" id="issue-title" placeholder="${t('quick_issue', 'Issue title...')}" maxlength="200">
                    </div>
                    <div class="form-group">
                        <label>${t('issue_description', 'Description')}</label>
                        <textarea id="issue-description" placeholder="${t('issue_description', 'Description...')}" rows="2"></textarea>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>${t('issue_type', 'Type')}</label>
                            <select id="issue-type">
                                <option value="Issue" selected>${t('type_issue', 'Issue')}</option>
                                <option value="Problem">${t('type_problem', 'Problem')}</option>
                                <option value="Suggestion">${t('type_suggestion', 'Suggestion')}</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>${t('issue_priority', 'Priority')}</label>
                            <select id="issue-priority">
                                <option value="Low">${t('priority_low', 'Low')}</option>
                                <option value="Medium" selected>${t('priority_medium', 'Medium')}</option>
                                <option value="High">${t('priority_high', 'High')}</option>
                                <option value="Critical">${t('priority_critical', 'Critical')}</option>
                            </select>
                        </div>
                    </div>
                    <button class="issue-create-btn" id="issue-create">
                        <i class="fa-solid fa-plus"></i> ${t('create_issue', 'Create Issue')}
                    </button>
                </div>
            </div>
        `;
    }

    function getRemindersHTML() {
        return `
            <div class="reminders-container">
                <div class="reminder-form">
                    <input type="text" id="reminder-title" placeholder="${t('quick_reminder', 'Reminder title...')}" maxlength="200">
                    <div class="reminder-time-row">
                        <input type="datetime-local" id="reminder-datetime">
                        <div class="reminder-presets">
                            <button class="preset-btn" data-preset="1h">${t('in_1_hour', '1h')}</button>
                            <button class="preset-btn" data-preset="tonight">${t('tonight', 'Tonight')}</button>
                            <button class="preset-btn" data-preset="tomorrow">${t('tomorrow', 'Tomorrow')}</button>
                            <button class="preset-btn" data-preset="week">${t('next_week', 'Week')}</button>
                            <button class="preset-btn" data-preset="daily">${t('daily', 'Daily')}</button>
                            <button class="preset-btn" data-preset="biweekly">${t('biweekly', '2 Weeks')}</button>
                        </div>
                    </div>
                    <div class="reminder-repeat-row">
                        <label>${t('repeat', 'Repeat')}:</label>
                        <select id="reminder-repeat">
                            <option value="">${t('no_repeat', 'No repeat')}</option>
                            <option value="daily">${t('daily', 'Daily')}</option>
                            <option value="weekly">${t('weekly', 'Weekly')}</option>
                            <option value="monthly">${t('monthly', 'Monthly')}</option>
                            <option value="weekdays">${t('weekdays', 'Weekdays')}</option>
                        </select>
                    </div>
                    <div class="reminder-link-row">
                        <input type="text" id="reminder-link" placeholder="${t('link_url', 'Link URL (optional)')}">
                        <input type="text" id="reminder-link-label" placeholder="${t('link_label', 'Link label')}">
                    </div>
                    <button class="reminder-add-btn" id="reminder-add">
                        <i class="fa-solid fa-bell"></i> ${t('add_reminder', 'Set Reminder')}
                    </button>
                </div>
                <div class="reminders-list" id="reminders-list">
                    <div class="reminders-empty">
                        <i class="fa-solid fa-bell-slash"></i>
                        <p>${t('no_reminders', 'No reminders')}</p>
                        <span>${t('no_reminders_desc', 'Set a reminder to get notified')}</span>
                    </div>
                </div>
            </div>
        `;
    }

    function getFavoritesHTML() {
        return `
            <div class="favorites-container">
                <div class="favorites-header">
                    <span>${t('favorites', 'Favorites')}</span>
                    <button class="add-favorite-btn" id="add-current-page" title="${t('add_current_page', 'Add Current Page')}">
                        <i class="fa-solid fa-plus"></i>
                    </button>
                </div>
                <div class="favorites-list" id="favorites-list">
                    <div class="favorites-empty">
                        <i class="fa-solid fa-star"></i>
                        <p>${t('no_favorites', 'No favorites yet')}</p>
                        <span>${t('no_favorites_desc', 'Add frequently used pages here')}</span>
                    </div>
                </div>
            </div>
        `;
    }

    // Bind Events
    function bindEvents() {
        // FAB click
        document.addEventListener('click', function(e) {
            const fabBtn = e.target.closest('#quick-tools-btn');
            const panelClose = e.target.closest('.quick-panel-close');
            const tabBtn = e.target.closest('.quick-tab');
            const toolCard = e.target.closest('.tool-card');

            if (fabBtn) {
                togglePanel();
                return;
            }

            if (panelClose) {
                closePanel();
                return;
            }

            if (tabBtn) {
                switchTool(tabBtn.dataset.tool);
                return;
            }

            if (toolCard) {
                switchTool(toolCard.dataset.tool);
                return;
            }

            // Click outside to close
            if (isPanelOpen && panelEl && !panelEl.contains(e.target) && !fabEl.contains(e.target)) {
                closePanel();
            }
        });

        // Calculator buttons
        document.addEventListener('click', function(e) {
            const calcBtn = e.target.closest('.calc-btn');
            if (calcBtn && isPanelOpen && currentTool === 'calculator') {
                handleCalcClick(calcBtn);
            }

            // Scientific mode toggle
            if (e.target.closest('.calc-mode-btn')) {
                const mode = e.target.closest('.calc-mode-btn').dataset.mode;
                calcScientificMode = mode === 'scientific';
                document.querySelectorAll('.calc-mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
                document.querySelector('.calc-scientific-buttons')?.classList.toggle('active', calcScientificMode);
            }

            // History toggle
            if (e.target.closest('#calc-history-toggle')) {
                document.getElementById('calc-history-panel')?.classList.toggle('active');
            }

            // History clear
            if (e.target.closest('#calc-history-clear')) {
                calcHistory = [];
                document.getElementById('calc-history-panel')?.classList.remove('active');
                renderCalcButtons();
            }

            // History item click
            if (e.target.closest('.calc-history-item')) {
                const expr = e.target.closest('.calc-history-item').dataset.expr;
                calcExpression = expr;
                document.getElementById('calc-expression').value = expr;
                document.getElementById('calc-history-panel')?.classList.remove('active');
            }

            // Scientific functions
            if (e.target.closest('[data-sci]') && currentTool === 'calculator') {
                const sciFunc = e.target.closest('[data-sci]').dataset.sci;
                handleScientificFunc(sciFunc);
            }
        });

        // Calc copy button
        document.addEventListener('click', function(e) {
            if (e.target.closest('#calc-copy')) {
                copyCalcResult();
            }
        });

        // Notes events
        document.addEventListener('click', function(e) {
            if (!isPanelOpen || currentTool !== 'notes') return;

            if (e.target.closest('#note-add')) {
                addNote();
            } else if (e.target.closest('.color-btn')) {
                document.querySelectorAll('.color-btn').forEach(b => b.classList.remove('active'));
                e.target.closest('.color-btn').classList.add('active');
            } else if (e.target.closest('.note-delete')) {
                deleteNote(e.target.closest('.note-item').dataset.id);
            } else if (e.target.closest('.note-pin')) {
                togglePinNote(e.target.closest('.note-item').dataset.id);
            } else if (e.target.closest('.note-edit')) {
                editNoteInline(e.target.closest('.note-item').dataset.id);
            }
        });

        // Notes search
        document.addEventListener('input', function(e) {
            if (e.target.id === 'notes-search') {
                notesSearchQuery = e.target.value;
                loadNotes();
            }
        });

        // Notes sort
        document.addEventListener('change', function(e) {
            if (e.target.id === 'notes-sort') {
                notesSortBy = e.target.value;
                loadNotes();
            }
        });

        // Task create
        document.addEventListener('click', function(e) {
            if (e.target.closest('#task-create') && isPanelOpen && currentTool === 'tasks') {
                createQuickTask();
            }

            // Task filters
            if (e.target.closest('.task-filter-btn') && isPanelOpen && currentTool === 'tasks') {
                tasksFilter = e.target.closest('.task-filter-btn').dataset.filter;
                document.querySelectorAll('.task-filter-btn').forEach(b => b.classList.toggle('active', b.dataset.filter === tasksFilter));
                // Filter display would be applied to loaded tasks
            }
        });

        // Issue create
        document.addEventListener('click', function(e) {
            if (e.target.closest('#issue-create') && isPanelOpen && currentTool === 'issues') {
                createQuickIssue();
            }
        });

        // Reminder events
        document.addEventListener('click', function(e) {
            if (!isPanelOpen || currentTool !== 'reminders') return;

            if (e.target.closest('#reminder-add')) {
                addReminder();
            } else if (e.target.closest('.preset-btn')) {
                setReminderPreset(e.target.closest('.preset-btn').dataset.preset);
            } else if (e.target.closest('.reminder-done')) {
                markReminderDone(e.target.closest('.reminder-item').dataset.id);
            } else if (e.target.closest('.reminder-snooze')) {
                showSnoozeOptions(e.target.closest('.reminder-item').dataset.id, e.target.closest('.reminder-snooze'));
            } else if (e.target.closest('.reminder-delete')) {
                deleteReminder(e.target.closest('.reminder-item').dataset.id);
            } else if (e.target.closest('.snooze-option')) {
                const snoozeMinutes = parseInt(e.target.closest('.snooze-option').dataset.minutes);
                const reminderId = e.target.closest('.snooze-dropdown')?.dataset.reminderId;
                if (reminderId) {
                    snoozeReminder(reminderId, snoozeMinutes);
                }
            }
        });

        // Favorites events
        document.addEventListener('click', function(e) {
            if (!isPanelOpen || currentTool !== 'favorites') return;

            if (e.target.closest('#add-current-page')) {
                addCurrentPageFavorite();
            } else if (e.target.closest('.fav-delete')) {
                deleteFavorite(e.target.closest('.fav-item').dataset.id);
            } else if (e.target.closest('.fav-item')) {
                const url = e.target.closest('.fav-item').dataset.url;
                if (url) {
                    window.location.href = url;
                }
            }
        });

        // Launcher search
        document.addEventListener('input', function(e) {
            if (e.target.id === 'launcher-search') {
                filterTools(e.target.value);
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Escape to close
            if (e.key === 'Escape' && isPanelOpen) {
                closePanel();
            }

            // Calculator keyboard support
            if (isPanelOpen && currentTool === 'calculator') {
                const calcDisplay = document.getElementById('calc-expression');
                if (!calcDisplay) return;

                if (e.key >= '0' && e.key <= '9') {
                    appendToCalc(e.key);
                } else if (e.key === '.') {
                    appendToCalc('.');
                } else if (e.key === '+' || e.key === '-' || e.key === '*' || e.key === '/') {
                    appendToCalc(e.key);
                } else if (e.key === '%') {
                    appendToCalc('%');
                } else if (e.key === 'Enter' || e.key === '=') {
                    e.preventDefault();
                    calculateResult();
                } else if (e.key === 'Backspace') {
                    e.preventDefault();
                    backspaceCalc();
                } else if (e.key === 'Escape') {
                    clearCalc();
                }
            }
        });

        // Close snooze dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.snooze-dropdown')) {
                document.querySelectorAll('.snooze-dropdown').forEach(d => d.remove());
            }
        });
    }

    // Filter tools in launcher
    function filterTools(query) {
        const cards = document.querySelectorAll('.tool-card');
        const lowerQuery = query.toLowerCase();
        cards.forEach(card => {
            const label = card.querySelector('.tool-card-label').textContent.toLowerCase();
            const desc = card.querySelector('.tool-card-desc').textContent.toLowerCase();
            const matches = label.includes(lowerQuery) || desc.includes(lowerQuery);
            card.style.display = matches ? '' : 'none';
        });
    }

    // Panel Toggle
    function togglePanel() {
        if (isPanelOpen) {
            closePanel();
        } else {
            openPanel();
        }
    }

    function openPanel() {
        isPanelOpen = true;
        panelEl.classList.add('open');
        fabEl.classList.add('active');
        fabEl.querySelector('.fa-flask').style.display = 'none';
        fabEl.querySelector('.quick-fab-close').style.display = 'inline';

        // Load data for current tool
        loadToolData(currentTool);

        // Focus appropriate element
        setTimeout(() => {
            if (currentTool === 'calculator') {
                document.getElementById('calc-expression')?.focus();
            } else if (currentTool === 'notes') {
                document.getElementById('note-content')?.focus();
            }
        }, 100);
    }

    function closePanel() {
        isPanelOpen = false;
        panelEl.classList.remove('open');
        fabEl.classList.remove('active');
        fabEl.querySelector('.fa-flask').style.display = 'inline';
        fabEl.querySelector('.quick-fab-close').style.display = 'none';
    }

    function switchTool(tool) {
        currentTool = tool;

        // Update tabs
        document.querySelectorAll('.quick-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tool === tool);
        });

        // Update content
        document.querySelectorAll('.quick-tool-content').forEach(content => {
            content.classList.toggle('active', content.id === `quick-tool-${tool}`);
        });

        // Load data
        loadToolData(tool);
    }

    // Load Data for Tools
    function loadToolData(tool) {
        switch (tool) {
            case 'notes':
                loadNotes();
                break;
            case 'reminders':
                loadReminders();
                break;
            case 'favorites':
                loadFavorites();
                break;
            case 'launcher':
                // Just render tool cards
                break;
        }
    }

    // Track recent tools
    function trackRecentTool(tool) {
        recentTools = recentTools.filter(t => t !== tool);
        recentTools.unshift(tool);
        recentTools = recentTools.slice(0, 6); // Keep only 6 recent
        try {
            localStorage.setItem('qt_recent_tools', JSON.stringify(recentTools));
        } catch (e) {}
    }

    // Calculator Functions
    function handleCalcClick(btn) {
        if (btn.dataset.num !== undefined) {
            appendToCalc(btn.dataset.num);
        } else if (btn.dataset.op !== undefined) {
            appendToCalc(btn.dataset.op);
        } else if (btn.dataset.action === '.') {
            appendToCalc('.');
        } else if (btn.dataset.action === 'clear') {
            clearCalc();
        } else if (btn.dataset.action === 'backspace') {
            backspaceCalc();
        } else if (btn.dataset.action === '%') {
            appendToCalc('%');
        } else if (btn.dataset.action === '=') {
            calculateResult();
        }
    }

    function handleScientificFunc(func) {
        const funcs = {
            'sin': Math.sin,
            'cos': Math.cos,
            'tan': Math.tan,
            'sqrt': Math.sqrt,
            'sq': (x) => x * x,
            'pi': Math.PI,
            'e': Math.E
        };

        if (func === 'pow') {
            appendToCalc('^');
            return;
        }

        if (funcs[func]) {
            const val = funcs[func];
            if (typeof val === 'function') {
                appendToCalc(func + '(');
            } else {
                appendToCalc(String(val));
            }
        }
    }

    function showSnoozeOptions(reminderId, btn) {
        // Remove existing dropdowns
        document.querySelectorAll('.snooze-dropdown').forEach(d => d.remove());

        const dropdown = document.createElement('div');
        dropdown.className = 'snooze-dropdown';
        dropdown.dataset.reminderId = reminderId;
        dropdown.innerHTML = SNOOZE_OPTIONS.map(opt =>
            `<button class="snooze-option" data-minutes="${opt.minutes}">${opt.label}</button>`
        ).join('');

        document.body.appendChild(dropdown);

        // Position near button
        const rect = btn.getBoundingClientRect();
        dropdown.style.top = rect.bottom + 'px';
        dropdown.style.left = rect.left + 'px';

        // Auto remove after 3 seconds
        setTimeout(() => {
            if (dropdown.parentNode) dropdown.remove();
        }, 3000);
    }

    function appendToCalc(val) {
        calcExpression += val;
        const display = document.getElementById('calc-expression');
        if (display) {
            display.value = calcExpression;
        }
    }

    function clearCalc() {
        calcExpression = '';
        const display = document.getElementById('calc-expression');
        const result = document.getElementById('calc-result');
        if (display) display.value = '';
        if (result) result.textContent = '';
    }

    function backspaceCalc() {
        calcExpression = calcExpression.slice(0, -1);
        const display = document.getElementById('calc-expression');
        if (display) display.value = calcExpression || '0';
    }

    async function calculateResult() {
        if (!calcExpression.trim()) return;

        try {
            const response = await fetch('/api/quick-tools/calculate', {
                method: 'POST',
                headers: getCsrfHeaders(),
                body: JSON.stringify({ expression: calcExpression })
            });

            const data = await response.json();

            if (data.success) {
                calcHistory.push({ expression: calcExpression, result: data.result });
                const result = document.getElementById('calc-result');
                if (result) {
                    result.textContent = `= ${data.result}`;
                }
                calcExpression = String(data.result);
                const display = document.getElementById('calc-expression');
                if (display) display.value = calcExpression;
            } else {
                const result = document.getElementById('calc-result');
                if (result) {
                    result.textContent = data.error || t('expression_error', 'Error');
                    result.style.color = 'var(--theme-danger, #ef4444)';
                }
                setTimeout(() => {
                    if (result) {
                        result.textContent = '';
                        result.style.color = '';
                    }
                }, 2000);
            }
        } catch (err) {
            console.error('Calc error:', err);
        }
    }

    async function copyCalcResult() {
        const result = document.getElementById('calc-result');
        if (!result || !result.textContent) return;

        const text = result.textContent.replace('= ', '');
        try {
            await navigator.clipboard.writeText(text);
            if (window.toast) {
                window.toast(t('result_copied', 'Result copied'), 'success');
            }
        } catch (err) {
            console.error('Copy failed:', err);
        }
    }

    // Notes Functions
    async function loadNotes() {
        try {
            const response = await fetch('/api/quick-tools/notes');
            const data = await response.json();

            if (data.success && data.notes) {
                renderNotes(data.notes);
            }
        } catch (err) {
            console.error('Load notes error:', err);
        }
    }

    function renderNotes(notes) {
        const list = document.getElementById('notes-list');
        if (!list) return;

        if (!notes || notes.length === 0) {
            list.innerHTML = `
                <div class="notes-empty">
                    <i class="fa-solid fa-note-sticky"></i>
                    <p>${t('no_notes', 'No notes yet')}</p>
                    <span>${t('no_notes_desc', 'Create a note to get started')}</span>
                </div>
            `;
            return;
        }

        list.innerHTML = notes.map(note => `
            <div class="note-item ${note.is_pinned ? 'pinned' : ''}" data-id="${note.id}">
                <div class="note-color-bar" style="background: ${getNoteColor(note.color)};"></div>
                <div class="note-content-wrapper">
                    <div class="note-title">${escapeHtml(note.title || '')}</div>
                    <div class="note-text">${escapeHtml(note.content)}</div>
                    <div class="note-time">${formatDate(note.created_at)}</div>
                </div>
                <div class="note-actions">
                    <button class="note-pin ${note.is_pinned ? 'active' : ''}" title="${t('pin_note', 'Pin')}">
                        <i class="fa-solid fa-thumbtack"></i>
                    </button>
                    <button class="note-delete" title="${t('delete_note', 'Delete')}">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    function getNoteColor(color) {
        const colors = {
            blue: '#3b82f6',
            green: '#22c55e',
            yellow: '#eab308',
            red: '#ef4444',
            purple: '#a855f7',
            gray: '#6b7280'
        };
        return colors[color] || colors.blue;
    }

    async function addNote() {
        const content = document.getElementById('note-content');
        const title = document.getElementById('note-title');
        const activeColor = document.querySelector('.color-btn.active');

        if (!content || !content.value.trim()) {
            if (window.toast) window.toast(t('quick_note', 'Note content required'), 'error');
            return;
        }

        try {
            const response = await fetch('/api/quick-tools/notes', {
                method: 'POST',
                headers: getCsrfHeaders(),
                body: JSON.stringify({
                    content: content.value.trim(),
                    title: title?.value.trim() || '',
                    color: activeColor?.dataset.color || 'blue'
                })
            });

            const data = await response.json();

            if (data.success) {
                content.value = '';
                if (title) title.value = '';
                loadNotes();
                if (window.toast) window.toast(t('quick_note', 'Note added'), 'success');
            } else {
                if (window.toast) window.toast(data.error || 'Error', 'error');
            }
        } catch (err) {
            console.error('Add note error:', err);
        }
    }

    async function deleteNote(id) {
        if (!confirm(t('delete_note', 'Delete this note?'))) return;

        try {
            const response = await fetch(`/api/quick-tools/notes/${id}`, {
                method: 'DELETE',
                headers: getCsrfHeaders()
            });

            const data = await response.json();

            if (data.success) {
                loadNotes();
            } else {
                if (window.toast) window.toast(data.error || 'Error', 'error');
            }
        } catch (err) {
            console.error('Delete note error:', err);
        }
    }

    async function togglePinNote(id) {
        const noteEl = document.querySelector(`.note-item[data-id="${id}"]`);
        const isPinned = noteEl?.classList.contains('pinned');

        try {
            const response = await fetch(`/api/quick-tools/notes/${id}`, {
                method: 'PUT',
                headers: getCsrfHeaders(),
                body: JSON.stringify({ is_pinned: isPinned ? 0 : 1 })
            });

            const data = await response.json();

            if (data.success) {
                loadNotes();
            }
        } catch (err) {
            console.error('Pin note error:', err);
        }
    }

    // Task Functions
    async function createQuickTask() {
        const title = document.getElementById('task-title');
        const description = document.getElementById('task-description');
        const priority = document.getElementById('task-priority');
        const dueDate = document.getElementById('task-due-date');

        if (!title || !title.value.trim()) {
            if (window.toast) window.toast(t('task_title', 'Task title required'), 'error');
            return;
        }

        try {
            const response = await fetch('/api/quick-tools/task/create', {
                method: 'POST',
                headers: getCsrfHeaders(),
                body: JSON.stringify({
                    title: title.value.trim(),
                    description: description?.value.trim() || '',
                    priority: priority?.value || 'Medium',
                    due_at: dueDate?.value || null
                })
            });

            const data = await response.json();

            if (data.success) {
                title.value = '';
                if (description) description.value = '';
                if (dueDate) dueDate.value = '';
                if (window.toast) window.toast(t('task_created', 'Task created'), 'success');

                // Optionally navigate to task
                if (data.task_url) {
                    setTimeout(() => {
                        window.location.href = data.task_url;
                    }, 1000);
                }
            } else {
                if (window.toast) window.toast(data.error || 'Error', 'error');
            }
        } catch (err) {
            console.error('Create task error:', err);
        }
    }

    // Issue Functions
    async function createQuickIssue() {
        const title = document.getElementById('issue-title');
        const description = document.getElementById('issue-description');
        const issueType = document.getElementById('issue-type');
        const priority = document.getElementById('issue-priority');

        if (!title || !title.value.trim()) {
            if (window.toast) window.toast(t('issue_title', 'Issue title required'), 'error');
            return;
        }

        try {
            const response = await fetch('/api/quick-tools/issue/create', {
                method: 'POST',
                headers: getCsrfHeaders(),
                body: JSON.stringify({
                    title: title.value.trim(),
                    description: description?.value.trim() || '',
                    issue_type: issueType?.value || 'Issue',
                    priority: priority?.value || 'Medium'
                })
            });

            const data = await response.json();

            if (data.success) {
                title.value = '';
                if (description) description.value = '';
                if (window.toast) window.toast(t('issue_created', 'Issue created'), 'success');

                if (data.issue_url) {
                    setTimeout(() => {
                        window.location.href = data.issue_url;
                    }, 1000);
                }
            } else {
                if (window.toast) window.toast(data.error || 'Error', 'error');
            }
        } catch (err) {
            console.error('Create issue error:', err);
        }
    }

    // Reminder Functions
    async function loadReminders() {
        try {
            const response = await fetch('/api/quick-tools/reminders');
            const data = await response.json();

            if (data.success && data.reminders) {
                renderReminders(data.reminders);
            }
        } catch (err) {
            console.error('Load reminders error:', err);
        }
    }

    function renderReminders(reminders) {
        const list = document.getElementById('reminders-list');
        if (!list) return;

        if (!reminders || reminders.length === 0) {
            list.innerHTML = `
                <div class="reminders-empty">
                    <i class="fa-solid fa-bell-slash"></i>
                    <p>${t('no_reminders', 'No reminders')}</p>
                    <span>${t('no_reminders_desc', 'Set a reminder to get notified')}</span>
                </div>
            `;
            return;
        }

        const now = new Date();
        list.innerHTML = reminders.map(rem => {
            const remindDate = new Date(rem.remind_at);
            const isDue = remindDate <= now;
            const isOverdue = isDue && !rem.is_done;

            return `
                <div class="reminder-item ${isOverdue ? 'overdue' : ''}" data-id="${rem.id}">
                    <div class="reminder-icon ${isOverdue ? 'overdue' : ''}">
                        <i class="fa-solid fa-bell${rem.is_done ? '-slash' : ''}"></i>
                    </div>
                    <div class="reminder-content">
                        <div class="reminder-title">${escapeHtml(rem.title)}</div>
                        <div class="reminder-time">${formatReminderTime(rem.remind_at)}</div>
                    </div>
                    <div class="reminder-actions">
                        ${!rem.is_done ? `
                            <button class="reminder-done" title="${t('mark_done', 'Done')}">
                                <i class="fa-solid fa-check"></i>
                            </button>
                            <button class="reminder-snooze" title="${t('snooze', 'Snooze')}">
                                <i class="fa-solid fa-clock"></i>
                            </button>
                        ` : ''}
                        <button class="reminder-delete" title="${t('delete_note', 'Delete')}">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // Update badge
        updateReminderBadge(reminders.filter(r => !r.is_done).length);
    }

    function formatReminderTime(dateStr) {
        const date = new Date(dateStr);
        const now = new Date();
        const diff = date - now;

        if (diff < 0) {
            return t('overdue', 'Overdue');
        }

        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 60) {
            return `${minutes}m`;
        } else if (hours < 24) {
            return `${hours}h`;
        } else if (days === 1) {
            return t('tomorrow', 'Tomorrow');
        } else {
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        }
    }

    function updateReminderBadge(count) {
        const badge = document.getElementById('quick-tools-badge');
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 9 ? '9+' : count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    async function addReminder() {
        const title = document.getElementById('reminder-title');
        const datetime = document.getElementById('reminder-datetime');
        const repeat = document.getElementById('reminder-repeat');
        const linkUrl = document.getElementById('reminder-link');
        const linkLabel = document.getElementById('reminder-link-label');

        if (!title || !title.value.trim()) {
            if (window.toast) window.toast(t('quick_reminder', 'Reminder title required'), 'error');
            return;
        }

        if (!datetime || !datetime.value) {
            if (window.toast) window.toast(t('remind_at', 'Set reminder time'), 'error');
            return;
        }

        try {
            const response = await fetch('/api/quick-tools/reminders', {
                method: 'POST',
                headers: getCsrfHeaders(),
                body: JSON.stringify({
                    title: title.value.trim(),
                    remind_at: datetime.value,
                    repeat: repeat?.value || '',
                    link_url: linkUrl?.value?.trim() || '',
                    link_label: linkLabel?.value?.trim() || ''
                })
            });

            const data = await response.json();

            if (data.success) {
                title.value = '';
                datetime.value = '';
                if (repeat) repeat.value = '';
                if (linkUrl) linkUrl.value = '';
                if (linkLabel) linkLabel.value = '';
                loadReminders();
                if (window.toast) window.toast(t('reminder_set', 'Reminder set'), 'success');
            } else {
                if (window.toast) window.toast(data.error || 'Error', 'error');
            }
        } catch (err) {
            console.error('Add reminder error:', err);
        }
    }

    function setReminderPreset(preset) {
        const datetime = document.getElementById('reminder-datetime');
        if (!datetime) return;

        const now = new Date();
        let newDate;

        switch (preset) {
            case '1h':
                newDate = new Date(now.getTime() + 3600000);
                break;
            case 'tonight':
                newDate = new Date(now);
                newDate.setHours(20, 0, 0, 0);
                if (newDate <= now) newDate.setDate(newDate.getDate() + 1);
                break;
            case 'tomorrow':
                newDate = new Date(now);
                newDate.setDate(newDate.getDate() + 1);
                newDate.setHours(9, 0, 0, 0);
                break;
            case 'week':
                newDate = new Date(now);
                newDate.setDate(newDate.getDate() + 7);
                newDate.setHours(9, 0, 0, 0);
                break;
            default:
                return;
        }

        datetime.value = newDate.toISOString().slice(0, 16);
    }

    async function markReminderDone(id) {
        try {
            const response = await fetch(`/api/quick-tools/reminders/${id}/done`, {
                method: 'POST',
                headers: getCsrfHeaders()
            });

            const data = await response.json();

            if (data.success) {
                loadReminders();
            }
        } catch (err) {
            console.error('Mark done error:', err);
        }
    }

    async function snoozeReminder(id, minutes = 30) {
        minutes = minutes || 30;
        try {
            const response = await fetch(`/api/quick-tools/reminders/${id}/snooze`, {
                method: 'POST',
                headers: getCsrfHeaders(),
                body: JSON.stringify({ minutes: minutes })
            });

            const data = await response.json();

            if (data.success) {
                loadReminders();
                if (window.toast) window.toast(t('snooze', 'Snoozed') + ` ${minutes}m`, 'info');
            }
        } catch (err) {
            console.error('Snooze error:', err);
        }
    }

    async function deleteReminder(id) {
        if (!confirm(t('delete_note', 'Delete this reminder?'))) return;

        try {
            const response = await fetch(`/api/quick-tools/reminders/${id}`, {
                method: 'DELETE',
                headers: getCsrfHeaders()
            });

            const data = await response.json();

            if (data.success) {
                loadReminders();
            }
        } catch (err) {
            console.error('Delete reminder error:', err);
        }
    }

    // Browser Notification for Reminders
    let notifiedReminderIds = new Set();

    async function requestReminderPermission() {
        if (!('Notification' in window)) return 'unsupported';
        if (Notification.permission === 'granted') return 'granted';
        if (Notification.permission === 'denied') return 'denied';
        const perm = await Notification.requestPermission();
        return perm;
    }

    async function showReminderNotification(title, body, reminderId) {
        if (Notification.permission !== 'granted') return;
        if (notifiedReminderIds.has(reminderId)) return; // Already notified

        notifiedReminderIds.add(reminderId);

        try {
            const reg = await navigator.serviceWorker.getRegistration();
            if (reg) {
                await reg.showNotification(title, {
                    body,
                    tag: `reminder-${reminderId}`,
                    icon: '/static/icon-notify.png',
                    badge: '/static/badge.png',
                    requireInteraction: true,
                    actions: [
                        { action: 'view', title: t('view', 'View') },
                        { action: 'dismiss', title: t('dismiss', 'Dismiss') }
                    ]
                });
            } else {
                new Notification(title, {
                    body,
                    icon: '/static/icon-notify.png'
                });
            }
        } catch (e) {
            console.warn('Notification error:', e);
        }
    }

    async function checkDueReminders() {
        // Request notification permission on init
        await requestReminderPermission();

        // Poll for due reminders every 30 seconds
        setInterval(async () => {
            try {
                const response = await fetch('/api/quick-tools/reminders/check-due');
                const data = await response.json();

                if (data.success && data.due && data.due.length > 0) {
                    data.due.forEach(rem => {
                        // Show browser notification
                        showReminderNotification(
                            t('reminder_set', 'Reminder'),
                            rem.title,
                            rem.id
                        );

                        // Also show toast
                        if (window.toast) {
                            window.toast(`${t('reminders', 'Reminder')}: ${rem.title}`, 'info');
                        }
                    });
                    loadReminders();
                    updateReminderBadge(data.due.length);
                }
            } catch (err) {
                console.error('Check reminders error:', err);
            }
        }, 30000);
    }

    // Analytics functions
    async function loadUsageAnalytics() {
        try {
            const response = await fetch('/api/quick-tools/analytics/usage?days=7');
            const data = await response.json();

            if (data.success && data.analytics) {
                // Update badge with reminder count if any due
                if (data.analytics.due_reminders) {
                    updateReminderBadge(data.analytics.due_reminders);
                }
            }
        } catch (err) {
            console.error('Load analytics error:', err);
        }
    }

    // Edit note inline
    function editNoteInline(noteId) {
        const noteEl = document.querySelector(`.note-item[data-id="${noteId}"]`);
        if (!noteEl) return;

        const contentEl = noteEl.querySelector('.note-text');
        const titleEl = noteEl.querySelector('.note-title');
        const currentContent = contentEl.textContent;
        const currentTitle = titleEl?.textContent || '';

        // Create edit form
        const editForm = document.createElement('div');
        editForm.className = 'note-edit-form';
        editForm.innerHTML = `
            <input type="text" class="note-edit-title" value="${escapeHtml(currentTitle)}" placeholder="Title">
            <textarea class="note-edit-content">${escapeHtml(currentContent)}</textarea>
            <div class="note-edit-actions">
                <button class="note-edit-save"><i class="fa-solid fa-check"></i> Save</button>
                <button class="note-edit-cancel"><i class="fa-solid fa-xmark"></i> Cancel</button>
            </div>
        `;

        // Replace note content with edit form
        noteEl.querySelector('.note-content-wrapper').style.display = 'none';
        noteEl.appendChild(editForm);

        // Bind save/cancel
        editForm.querySelector('.note-edit-save').addEventListener('click', () => saveNoteInline(noteId, editForm));
        editForm.querySelector('.note-edit-cancel').addEventListener('click', () => {
            noteEl.querySelector('.note-content-wrapper').style.display = '';
            editForm.remove();
        });
    }

    async function saveNoteInline(noteId, editForm) {
        const title = editForm.querySelector('.note-edit-title').value;
        const content = editForm.querySelector('.note-edit-content').value;

        if (!content.trim()) {
            if (window.toast) window.toast(t('content_required', 'Content is required'), 'error');
            return;
        }

        try {
            const response = await fetch(`/api/quick-tools/notes/${noteId}`, {
                method: 'PUT',
                headers: getCsrfHeaders(),
                body: JSON.stringify({ title, content })
            });

            const data = await response.json();

            if (data.success) {
                loadNotes();
                if (window.toast) window.toast(t('note_updated', 'Note updated'), 'success');
            } else {
                if (window.toast) window.toast(data.error || 'Error', 'error');
            }
        } catch (err) {
            console.error('Update note error:', err);
        }
    }

    // Re-render calc buttons for history update
    function renderCalcButtons() {
        const calcContent = document.getElementById('quick-tool-calculator');
        if (calcContent) {
            const activeTab = document.querySelector('.quick-tab.active');
            const tool = activeTab ? activeTab.dataset.tool : 'calculator';
            if (tool === 'calculator') {
                // Re-render just the calculator portion
                calcContent.innerHTML = getCalculatorHTML();
            }
        }
    }

    // Favorites Functions
    async function loadFavorites() {
        try {
            const response = await fetch('/api/quick-tools/favorites');
            const data = await response.json();

            if (data.success && data.favorites) {
                renderFavorites(data.favorites);
                updateSidebarFavorites(data.favorites);
            }
        } catch (err) {
            console.error('Load favorites error:', err);
        }
    }

    function updateSidebarFavorites(favorites) {
        const container = document.getElementById('sidebar-favorites-list');
        if (!container) return;

        if (!favorites || favorites.length === 0) {
            container.innerHTML = `
                <div class="sidebar-submenu-group-label text-center py-4 text-theme-muted">
                    <i class="fa-solid fa-star text-lg mb-2 opacity-50 sidebar-favorites-star"></i>
                    <p class="text-xs">${t('no_favorites', 'No favorites yet')}</p>
                    <span class="text-xs opacity-70">${t('add_favorites_hint', 'Click + to add pages')}</span>
                </div>
            `;
            return;
        }

        container.innerHTML = favorites.map(fav => `
            <a href="${escapeHtml(fav.url)}" class="sidebar-submenu-link flex items-center gap-2 py-2">
                <i class="fa-solid ${fav.icon || 'fa-star'} sidebar-favorites-star"></i>
                <span class="flex-1 truncate">${escapeHtml(fav.label)}</span>
            </a>
        `).join('');
    }

    function renderFavorites(favorites) {
        const list = document.getElementById('favorites-list');
        if (!list) return;

        if (!favorites || favorites.length === 0) {
            list.innerHTML = `
                <div class="favorites-empty">
                    <i class="fa-solid fa-star"></i>
                    <p>${t('no_favorites', 'No favorites yet')}</p>
                    <span>${t('no_favorites_desc', 'Add frequently used pages here')}</span>
                </div>
            `;
            return;
        }

        list.innerHTML = favorites.map(fav => `
            <div class="fav-item" data-id="${fav.id}" data-url="${escapeHtml(fav.url)}">
                <div class="fav-icon" style="background: ${getFavColor(fav.color)};">
                    <i class="fa-solid ${fav.icon || 'fa-star'}"></i>
                </div>
                <div class="fav-label">${escapeHtml(fav.label)}</div>
                <button class="fav-delete" title="${t('remove_favorite', 'Remove')}">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
        `).join('');
    }

    function getFavColor(color) {
        const colors = {
            blue: '#3b82f6',
            green: '#22c55e',
            yellow: '#eab308',
            red: '#ef4444',
            purple: '#a855f7',
            gray: '#6b7280',
            orange: '#f97316'
        };
        return colors[color] || colors.blue;
    }

    async function addCurrentPageFavorite() {
        const url = window.location.pathname;
        const label = document.title.replace(/ - .*$/, '').trim() || url;

        try {
            const response = await fetch('/api/quick-tools/favorites/add-current', {
                method: 'POST',
                headers: getCsrfHeaders(),
                body: JSON.stringify({ url, label })
            });

            const data = await response.json();

            if (data.success) {
                loadFavorites();
                if (window.toast) window.toast(t('bookmark_added', 'Bookmark added'), 'success');
            } else {
                if (window.toast) window.toast(data.error || 'Error', 'error');
            }
        } catch (err) {
            console.error('Add favorite error:', err);
        }
    }

    async function deleteFavorite(id) {
        try {
            const response = await fetch(`/api/quick-tools/favorites/${id}`, {
                method: 'DELETE',
                headers: getCsrfHeaders()
            });

            const data = await response.json();

            if (data.success) {
                loadFavorites();
            }
        } catch (err) {
            console.error('Delete favorite error:', err);
        }
    }

    // Preferences
    async function loadPreferences() {
        try {
            const response = await fetch('/api/quick-tools/preferences');
            const data = await response.json();

            if (data.success && data.preferences) {
                // Apply preferences
                if (data.preferences.default_tool) {
                    switchTool(data.preferences.default_tool);
                }
            }
        } catch (err) {
            console.error('Load preferences error:', err);
        }
    }

    // Utilities
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose globally accessible functions for sidebar integration
    window.openQuickToolsPanel = function(tool) {
        if (!isPanelOpen) {
            openPanel();
        }
        if (tool) {
            switchTool(tool);
        }
    };

    window.loadSidebarFavorites = function() {
        loadFavorites();
    };
})();
