document.addEventListener('DOMContentLoaded', () => {
    const loadDashboardData = async () => {
        try {
            const response = await fetch('/api/dashboard/');
            const data = await response.json();
            
            // Aggiorna UI
            document.getElementById('teocoin-balance').textContent = data.user.teo_coins;
            populateNotifications(data.notifications);
            populateTransactions(data.recent_transactions);
            
        } catch (error) {
            console.error('Error loading dashboard:', error);
        }
    };
    
    loadDashboardData();
});