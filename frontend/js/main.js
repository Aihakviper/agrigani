/**
 * AgriGani Homepage
 * Main functionality for the landing page
 */

document.addEventListener('DOMContentLoaded', () => {
    // Load statistics
    loadStatistics();
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // Add scroll animations
    setupScrollAnimations();
});

/**
 * Load platform statistics
 */
async function loadStatistics() {
    try {
        const stats = await Utils.apiRequest(API_CONFIG.getEndpoint('DIAGNOSES_STATS'));
        
        // Animate total diagnoses counter
        const totalElement = document.getElementById('totalDiagnoses');
        if (totalElement && stats.total_diagnoses) {
            animateCounter(totalElement, 0, stats.total_diagnoses, 2000);
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
        // Set default value on error
        const totalElement = document.getElementById('totalDiagnoses');
        if (totalElement) {
            totalElement.textContent = '1000+';
        }
    }
}

/**
 * Animate counter from start to end
 */
function animateCounter(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16); // 60fps
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= end) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current).toLocaleString();
    }, 16);
}

/**
 * Setup scroll animations
 */
function setupScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe feature cards
    document.querySelectorAll('.feature-card').forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `all 0.6s ease ${index * 0.1}s`;
        observer.observe(card);
    });
}
