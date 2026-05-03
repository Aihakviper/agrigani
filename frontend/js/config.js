/**
 * AgriGani Frontend Configuration
 * API endpoints and settings
 */

const API_CONFIG = {
    // Base URL - Change this to your backend URL
    BASE_URL: 'http://localhost:8000',
    
    // API Version
    API_VERSION: 'v1',
    
    // Full API base path
    get API_BASE() {
        return `${this.BASE_URL}/api/${this.API_VERSION}`;
    },
    
    // Endpoints
    ENDPOINTS: {
        FARMERS: '/farmers/',
        DISEASES: '/diseases/',
        VENDORS: '/vendors/',
        DIAGNOSES: '/diagnoses/',
        DIAGNOSES_STATS: '/diagnoses/statistics/',
    },
    
    // Get full endpoint URL
    getEndpoint(endpoint) {
        return `${this.API_BASE}${this.ENDPOINTS[endpoint]}`;
    },
    
    // Request timeout (ms)
    TIMEOUT: 30000,
    
    // Max file size (5MB)
    MAX_FILE_SIZE: 5 * 1024 * 1024,
    
    // Allowed file types
    ALLOWED_FILE_TYPES: ['image/jpeg', 'image/png', 'image/jpg'],
};

// Export for use in other files
window.API_CONFIG = API_CONFIG;
