document.addEventListener('DOMContentLoaded', function() {
    const apiUrl = '/api/dashboard/';
    const updateInterval = 30000; // 30 secondi

    async function fetchDashboardData() {
        try {
            const response = await fetch(apiUrl, {
                headers: {
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            });
            
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            updateDashboardUI(data);
            
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
            showErrorMessage();
        }
    }

    function getAuthToken() {
        return document.cookie
            .split('; ')
            .find(row => row.startsWith('access_token='))
            ?.split('=')[1];
    }

    function updateDashboardUI(data) {
        // Aggiorna TeoCoins
        document.getElementById('teocoin-balance').textContent = data.user.teo_coins;
        
        // Aggiorna Lezioni
        const lessonsContainer = document.getElementById('lessons-list');
        lessonsContainer.innerHTML = data.lessons.map(lesson => `
            <div class="lesson-card bg-white p-4 rounded-lg shadow mb-4">
                <h3 class="text-lg font-semibold">${lesson.title}</h3>
                <p class="text-gray-600">Insegnante: ${lesson.teacher.username}</p>
                <div class="mt-2 text-blue-600">${lesson.price} TeoCoin</div>
            </div>
        `).join('');

        // Aggiorna Transazioni
        const transactionsContainer = document.getElementById('transactions-list');
        transactionsContainer.innerHTML = data.transactions.map(transaction => `
            <div class="transaction-item p-2 border-b">
                <div class="flex justify-between">
                    <span>${transaction.transaction_type}</span>
                    <span class="${transaction.amount < 0 ? 'text-red-600' : 'text-green-600'}">
                        ${transaction.amount} TC
                    </span>
                </div>
                <div class="text-sm text-gray-500">${new Date(transaction.created_at).toLocaleDateString()}</div>
            </div>
        `).join('');
    }

    function showErrorMessage() {
        const container = document.getElementById('dashboard-container');
        container.innerHTML = `
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded" role="alert">
                Impossibile caricare i dati. Riprova più tardi.
            </div>
        `;
    }

    // Aggiornamento iniziale e periodico
    fetchDashboardData();
    setInterval(fetchDashboardData, updateInterval);
});