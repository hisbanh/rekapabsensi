// Custom JavaScript for SIPA Beta  Admin with Unfold

document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card, .metric-card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });

    // Add loading state to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
            }
        });
    });

    // Enhanced table interactions
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('click', function(e) {
                // Don't trigger if clicking on a link or button
                if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON' || e.target.closest('a') || e.target.closest('button')) {
                    return;
                }
                
                // Add selection highlight
                rows.forEach(r => r.classList.remove('selected'));
                this.classList.add('selected');
            });
        });
    });

    // Auto-refresh for dashboard (every 5 minutes)
    if (window.location.pathname.includes('/admin/')) {
        setInterval(() => {
            // Only refresh if user is active (has interacted in last 5 minutes)
            if (document.lastInteraction && Date.now() - document.lastInteraction < 300000) {
                // Refresh dashboard widgets or specific content
                refreshDashboardStats();
            }
        }, 300000); // 5 minutes
    }

    // Track user interaction
    document.addEventListener('click', () => {
        document.lastInteraction = Date.now();
    });

    document.addEventListener('keypress', () => {
        document.lastInteraction = Date.now();
    });
});

// Function to refresh dashboard statistics
function refreshDashboardStats() {
    const statsElements = document.querySelectorAll('.metric-number');
    if (statsElements.length > 0) {
        // Add subtle loading indicator
        statsElements.forEach(el => {
            el.style.opacity = '0.7';
        });

        // Simulate refresh (in real implementation, this would be an AJAX call)
        setTimeout(() => {
            statsElements.forEach(el => {
                el.style.opacity = '1';
            });
        }, 1000);
    }
}

// Utility function for showing notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        animation: slideIn 0.3s ease-out;
    `;

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Add CSS for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .selected {
        background-color: #e3f2fd !important;
    }
`;
document.head.appendChild(style);