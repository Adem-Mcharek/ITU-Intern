/**
 * WebTV Processor - Live Status Updates & UI Interactions
 * Handles real-time status updates, theme switching, and enhanced UX
 */

// Theme Management
(function() {
    'use strict';
    
    const getStoredTheme = () => localStorage.getItem('theme');
    const setStoredTheme = theme => localStorage.setItem('theme', theme);
    
    const getPreferredTheme = () => {
        const storedTheme = getStoredTheme();
        if (storedTheme) {
            return storedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    };
    
    const setTheme = theme => {
        if (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-bs-theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-bs-theme', theme);
        }
    };
    
    const showActiveTheme = (theme, focus = false) => {
        const themeSwitcher = document.querySelector('#themeDropdown');
        if (!themeSwitcher) return;
        
        const themeSwitcherText = document.querySelector('#bd-theme-text');
        const activeThemeIcon = document.querySelector('.theme-icon-active use');
        const btnToActive = document.querySelector(`[data-bs-theme-value="${theme}"]`);
        const svgOfActiveBtn = btnToActive ? btnToActive.querySelector('svg use').getAttribute('href') : null;
        
        if (activeThemeIcon && svgOfActiveBtn) {
            activeThemeIcon.setAttribute('href', svgOfActiveBtn);
        }
        
        document.querySelectorAll('[data-bs-theme-value]').forEach(element => {
            element.classList.remove('active');
            element.setAttribute('aria-pressed', 'false');
        });
        
        if (btnToActive) {
            btnToActive.classList.add('active');
            btnToActive.setAttribute('aria-pressed', 'true');
        }
        
        if (focus && themeSwitcher) {
            themeSwitcher.focus();
        }
    };
    
    // Initialize theme
    setTheme(getPreferredTheme());
    
    // Handle theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        const storedTheme = getStoredTheme();
        if (storedTheme !== 'light' && storedTheme !== 'dark') {
            setTheme(getPreferredTheme());
        }
    });
    
    // Theme switcher event listeners
    document.addEventListener('DOMContentLoaded', () => {
        showActiveTheme(getPreferredTheme());
        
        document.querySelectorAll('[data-bs-theme-value]').forEach(toggle => {
            toggle.addEventListener('click', () => {
                const theme = toggle.getAttribute('data-bs-theme-value');
                setStoredTheme(theme);
                setTheme(theme);
                showActiveTheme(theme, true);
            });
        });
    });
})();

// Live Status Updates
class StatusUpdater {
    constructor() {
        this.updateInterval = 5000; // 5 seconds
        this.intervals = new Map();
        this.init();
    }
    
    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.startStatusUpdates();
        });
        
        // Listen for HTMX events
        document.addEventListener('htmx:afterSwap', (event) => {
            if (event.target.id === 'status-update') {
                this.handleStatusUpdate(event.target);
            }
        });
    }
    
    startStatusUpdates() {
        // Find elements that need status updates
        const statusElements = document.querySelectorAll('[hx-trigger*="every"]');
        statusElements.forEach(element => {
            const meetingId = this.extractMeetingId(element);
            if (meetingId) {
                this.scheduleStatusUpdate(meetingId, element);
            }
        });
    }
    
    extractMeetingId(element) {
        const hxGet = element.getAttribute('hx-get');
        if (hxGet) {
            const match = hxGet.match(/\/api\/status\/(\d+)/);
            return match ? match[1] : null;
        }
        return null;
    }
    
    scheduleStatusUpdate(meetingId, element) {
        const intervalId = setInterval(() => {
            this.updateStatus(meetingId, element);
        }, this.updateInterval);
        
        this.intervals.set(meetingId, intervalId);
    }
    
    async updateStatus(meetingId, element) {
        try {
            const response = await fetch(`/api/status/${meetingId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.handleStatusResponse(data, element, meetingId);
        } catch (error) {
            console.error('Status update failed:', error);
        }
    }
    
    handleStatusResponse(data, element, meetingId) {
        // Update status display
        const statusContainer = element.querySelector('#status-update');
        if (statusContainer) {
            this.updateStatusDisplay(statusContainer, data);
        }
        
        // Update queue information
        this.updateQueueInfo(data);
        
        // Stop polling if processing is complete
        if (data.status === 'completed' || data.status === 'done' || data.status === 'error') {
            this.stopStatusUpdate(meetingId);
            
            // Reload page after a short delay to show final state
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        }
    }
    
    updateStatusDisplay(container, data) {
        const spinner = container.querySelector('.spinner-border');
        const statusText = container.querySelector('span');
        
        if (data.status === 'completed' || data.status === 'done') {
            if (spinner) spinner.style.display = 'none';
            if (statusText) {
                statusText.innerHTML = `
                    <svg class="bi text-success me-2" width="16" height="16" fill="currentColor">
                        <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"/>
                    </svg>
                    Processing completed successfully! Refreshing page...
                `;
                statusText.className = 'text-success';
            }
        } else if (data.status === 'error') {
            if (spinner) spinner.style.display = 'none';
            if (statusText) {
                statusText.innerHTML = `
                    <svg class="bi text-danger me-2" width="16" height="16" fill="currentColor">
                        <path d="M5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"/>
                    </svg>
                    Processing failed. ${data.error_message || 'Please try again.'}
                `;
                statusText.className = 'text-danger';
            }
        } else if (data.status === 'processing') {
            if (statusText) {
                statusText.textContent = 'Processing in progress... This may take several minutes depending on video length.';
            }
        } else if (data.status === 'queued') {
            if (statusText) {
                let queueText = 'Queued for processing';
                if (data.queue_position && data.queue_position > 0) {
                    queueText += ` (Position: ${data.queue_position})`;
                }
                if (data.estimated_wait_time) {
                    queueText += ` - Estimated wait: ${data.estimated_wait_time}`;
                }
                statusText.textContent = queueText;
            }
        }
    }
    
    updateQueueInfo(data) {
        // Update any queue information displays on the page
        const queueInfoElements = document.querySelectorAll('.queue-info');
        queueInfoElements.forEach(element => {
            if (data.queue_position && data.queue_position > 0) {
                element.textContent = `Position in queue: ${data.queue_position}`;
                element.style.display = 'block';
            } else {
                element.style.display = 'none';
            }
        });
        
        // Update queue length display for admin/developer panels
        const queueLengthElements = document.querySelectorAll('.queue-length');
        queueLengthElements.forEach(element => {
            if (data.queue_length !== undefined) {
                element.textContent = data.queue_length;
            }
        });
        
        // Update currently processing display
        const currentlyProcessingElements = document.querySelectorAll('.currently-processing');
        currentlyProcessingElements.forEach(element => {
            if (data.currently_processing_id) {
                element.style.display = 'block';
                const linkElement = element.querySelector('a');
                if (linkElement) {
                    linkElement.href = `/meetings/${data.currently_processing_id}`;
                }
            } else {
                element.style.display = 'none';
            }
        });
    }
    
    stopStatusUpdate(meetingId) {
        const intervalId = this.intervals.get(meetingId);
        if (intervalId) {
            clearInterval(intervalId);
            this.intervals.delete(meetingId);
        }
    }
    
    handleStatusUpdate(target) {
        // Handle successful HTMX status updates
        console.log('Status updated via HTMX');
    }
}

// Toast Notifications
class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }
    
    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.container = document.getElementById('toast-container');
            if (!this.container) {
                this.createContainer();
            }
        });
    }
    
    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(this.container);
    }
    
    show(message, type = 'info', duration = 5000) {
        if (!this.container) {
            this.createContainer();
        }
        
        const toastId = 'toast-' + Date.now();
        const iconMap = {
            success: 'M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z',
            error: 'M5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z',
            warning: 'M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z',
            info: 'M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z'
        };
        
        const toastHTML = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-autohide="true" data-bs-delay="${duration}">
                <div class="toast-header">
                    <svg class="bi text-${type} me-2" width="16" height="16" fill="currentColor">
                        <path d="${iconMap[type] || iconMap.info}"/>
                    </svg>
                    <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                    <small class="text-muted">now</small>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        this.container.insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Clean up after toast is hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    }
}

// Search Enhancement
class SearchEnhancer {
    constructor() {
        this.debounceTimer = null;
        this.debounceDelay = 300;
        this.init();
    }
    
    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.enhanceSearchForms();
            this.addKeyboardShortcuts();
        });
    }
    
    enhanceSearchForms() {
        const searchInputs = document.querySelectorAll('input[type="search"], input[name="query"]');
        searchInputs.forEach(input => {
            this.addSearchEnhancements(input);
        });
    }
    
    addSearchEnhancements(input) {
        // Add clear button
        const clearButton = this.createClearButton(input);
        
        // Add debounced search
        input.addEventListener('input', (e) => {
            this.handleSearchInput(e.target);
        });
        
        // Show/hide clear button
        input.addEventListener('input', () => {
            clearButton.style.display = input.value ? 'block' : 'none';
        });
    }
    
    createClearButton(input) {
        const wrapper = document.createElement('div');
        wrapper.className = 'position-relative';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        
        const clearButton = document.createElement('button');
        clearButton.type = 'button';
        clearButton.className = 'btn btn-link position-absolute top-50 end-0 translate-middle-y pe-3';
        clearButton.style.display = 'none';
        clearButton.innerHTML = '×';
        clearButton.addEventListener('click', () => {
            input.value = '';
            input.focus();
            clearButton.style.display = 'none';
            this.handleSearchInput(input);
        });
        
        wrapper.appendChild(clearButton);
        return clearButton;
    }
    
    handleSearchInput(input) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            // Trigger any custom search logic here
            this.performSearch(input);
        }, this.debounceDelay);
    }
    
    performSearch(input) {
        // Custom search logic can be added here
        console.log('Searching for:', input.value);
    }
    
    addKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K to focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('input[type="search"], input[name="query"]');
                if (searchInput) {
                    searchInput.focus();
                }
            }
        });
    }
}

// Copy to Clipboard Enhancement
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            window.toastManager.show('Link copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Could not copy text: ', err);
            window.toastManager.show('Failed to copy link', 'error');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            window.toastManager.show('Link copied to clipboard!', 'success');
        } catch (err) {
            console.error('Could not copy text: ', err);
            window.toastManager.show('Failed to copy link', 'error');
        } finally {
            document.body.removeChild(textArea);
        }
    }
}

// Initialize all managers
document.addEventListener('DOMContentLoaded', () => {
    window.statusUpdater = new StatusUpdater();
    window.toastManager = new ToastManager();
    window.searchEnhancer = new SearchEnhancer();
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover focus'
        });
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Add loading states to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.classList.add('loading');
                
                // Re-enable after 10 seconds as fallback
                setTimeout(() => {
                    submitButton.disabled = false;
                    submitButton.classList.remove('loading');
                }, 10000);
            }
        });
    });
});

// Expose utility functions globally
window.copyToClipboard = copyToClipboard;
window.showToast = (message, type = 'info') => {
    if (window.toastManager) {
        window.toastManager.show(message, type);
    }
}; 