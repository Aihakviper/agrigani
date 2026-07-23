<<<<<<< HEAD
/**
 * AgriGani Utility Functions
 */

const Utils = {
    /**
     * Make API request with error handling
     */
    async apiRequest(url, options = {}) {
        try {
            const token = this.getAuthToken();
            const headers = {
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
                ...options.headers,
            };

            const response = await fetch(url, {
                ...options,
                headers,
            });

            if (!response.ok) {
                let message = `API request failed (${response.status})`;

                try {
                    const error = await response.json();
                    message = error.detail || error.message || error.error || this.formatApiErrors(error) || message;
                } catch (_) {
                    const text = await response.text();
                    if (text) {
                        message = text;
                    }
                }

                if (response.status === 401) {
                    this.clearAuth();
                    const current = encodeURIComponent(window.location.pathname.split('/').pop() || 'index.html');
                    window.location.href = `login.html?next=${current}`;
                }

                throw new Error(message);
            }

            if (response.status === 204) {
                return null;
            }

            const text = await response.text();
            return text ? JSON.parse(text) : null;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * Format date to readable string
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-NG', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    },

    formatApiErrors(error) {
        if (!error || typeof error !== 'object') return '';

        return Object.entries(error)
            .map(([field, value]) => {
                const text = Array.isArray(value) ? value.join(', ') : String(value);
                return field === 'non_field_errors' ? text : `${field}: ${text}`;
            })
            .join(' ');
    },

    getAuthToken() {
        return localStorage.getItem('agrigani_token');
    },

    setAuth(session) {
        localStorage.setItem('agrigani_token', session.token);
        localStorage.setItem('agrigani_user', JSON.stringify(session.user));
    },

    clearAuth() {
        localStorage.removeItem('agrigani_token');
        localStorage.removeItem('agrigani_user');
    },

    getAuthUser() {
        return this.getFromLocalStorage('agrigani_user');
    },

    requireAuth() {
        if (!this.getAuthToken()) {
            const current = encodeURIComponent(window.location.pathname.split('/').pop() || 'index.html');
            window.location.href = `login.html?next=${current}`;
            return false;
        }
        return true;
    },

    updateAuthNav(activePage = '') {
        const nav = document.querySelector('.navbar-nav');
        if (!nav) return;

        const isLoggedIn = Boolean(this.getAuthToken());
        const profileActive = activePage === 'profile' ? ' active' : '';
        const authHtml = isLoggedIn
            ? `
                <li class="nav-item"><a class="nav-link${profileActive}" href="profile.html">Profile</a></li>
                <li class="nav-item"><button type="button" class="nav-link btn btn-link" id="logoutButton">Logout</button></li>
            `
            : '<li class="nav-item"><a class="nav-link" href="login.html">Login</a></li>';

        nav.insertAdjacentHTML('beforeend', authHtml);
        const logoutButton = document.getElementById('logoutButton');
        if (logoutButton) {
            logoutButton.addEventListener('click', () => {
                this.clearAuth();
                window.location.href = 'index.html';
            });
        }
    },

    /**
     * Point stale local media URLs at the active API server.
     */
    resolveMediaUrl(url) {
        if (!url) return '';

        return url.replace(
            /^http:\/\/(localhost|127\.0\.0\.1):8000(?=\/media\/)/,
            API_CONFIG.BASE_URL.replace(/\/$/, '')
        );
    },

    /**
     * Validate image file
     */
    validateImage(file) {
        // Check file type
        if (!API_CONFIG.ALLOWED_FILE_TYPES.includes(file.type)) {
            throw new Error('Please upload a JPEG or PNG image');
        }

        // Check file size
        if (file.size > API_CONFIG.MAX_FILE_SIZE) {
            throw new Error(`File size must be less than ${this.formatFileSize(API_CONFIG.MAX_FILE_SIZE)}`);
        }

        return true;
    },

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show`;
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    },

    /**
     * Create toast container if it doesn't exist
     */
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
        `;
        document.body.appendChild(container);
        return container;
    },

    /**
     * Get confidence level class
     */
    getConfidenceClass(confidence) {
        if (confidence >= 80) return 'confidence-high';
        if (confidence >= 60) return 'confidence-medium';
        return 'confidence-low';
    },

    /**
     * Get confidence level text
     */
    getConfidenceText(confidence) {
        if (confidence >= 80) return 'High Confidence';
        if (confidence >= 60) return 'Medium Confidence';
        return 'Low Confidence';
    },

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Save to local storage
     */
    saveToLocalStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    },

    /**
     * Get from local storage
     */
    getFromLocalStorage(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return null;
        }
    },

    /**
     * Format vendor type
     */
    formatVendorType(type) {
        const types = {
            'AGRO_DEALER': 'Agricultural Dealer',
            'VET_CLINIC': 'Veterinary Clinic',
            'PHARMACY': 'Agricultural Pharmacy'
        };
        return types[type] || type;
    },

    /**
     * Get disease severity badge
     */
    getSeverityBadge(level) {
        const badges = {
            1: '<span class="badge bg-info">Low</span>',
            2: '<span class="badge bg-success">Moderate</span>',
            3: '<span class="badge bg-warning">Medium</span>',
            4: '<span class="badge bg-danger">High</span>',
            5: '<span class="badge bg-danger">Critical</span>'
        };
        return badges[level] || '';
    },

    /**
     * Truncate text
     */
    truncate(text, length = 100) {
        if (!text) return '';
        return text.length > length ? text.substring(0, length) + '...' : text;
    }
};

// Make Utils available globally
window.Utils = Utils;
=======
/**
 * AgriGani Utility Functions
 */

const Utils = {
    /**
     * Make API request with error handling
     */
    async apiRequest(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...options.headers,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || error.message || 'API request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * Format date to readable string
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-NG', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    },

    /**
     * Validate image file
     */
    validateImage(file) {
        // Check file type
        if (!API_CONFIG.ALLOWED_FILE_TYPES.includes(file.type)) {
            throw new Error('Please upload a JPEG or PNG image');
        }

        // Check file size
        if (file.size > API_CONFIG.MAX_FILE_SIZE) {
            throw new Error(`File size must be less than ${this.formatFileSize(API_CONFIG.MAX_FILE_SIZE)}`);
        }

        return true;
    },

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show`;
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    },

    /**
     * Create toast container if it doesn't exist
     */
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
        `;
        document.body.appendChild(container);
        return container;
    },

    /**
     * Get confidence level class
     */
    getConfidenceClass(confidence) {
        if (confidence >= 80) return 'confidence-high';
        if (confidence >= 60) return 'confidence-medium';
        return 'confidence-low';
    },

    /**
     * Get confidence level text
     */
    getConfidenceText(confidence) {
        if (confidence >= 80) return 'High Confidence';
        if (confidence >= 60) return 'Medium Confidence';
        return 'Low Confidence';
    },

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Save to local storage
     */
    saveToLocalStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    },

    /**
     * Get from local storage
     */
    getFromLocalStorage(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return null;
        }
    },

    /**
     * Format vendor type
     */
    formatVendorType(type) {
        const types = {
            'AGRO_DEALER': 'Agricultural Dealer',
            'VET_CLINIC': 'Veterinary Clinic',
            'PHARMACY': 'Agricultural Pharmacy'
        };
        return types[type] || type;
    },

    /**
     * Get disease severity badge
     */
    getSeverityBadge(level) {
        const badges = {
            1: '<span class="badge bg-info">Low</span>',
            2: '<span class="badge bg-success">Moderate</span>',
            3: '<span class="badge bg-warning">Medium</span>',
            4: '<span class="badge bg-danger">High</span>',
            5: '<span class="badge bg-danger">Critical</span>'
        };
        return badges[level] || '';
    },

    /**
     * Truncate text
     */
    truncate(text, length = 100) {
        if (!text) return '';
        return text.length > length ? text.substring(0, length) + '...' : text;
    }
};

// Make Utils available globally
window.Utils = Utils;
>>>>>>> e6e80e1585eab5abf6fb939fd61354d35f8bd21e
