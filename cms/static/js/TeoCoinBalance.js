class TeoCoinBalance extends HTMLElement {
    constructor() {
        super();
        this.observer = new MutationObserver(() => this.updateBalance());
    }

    connectedCallback() {
        this.observer.observe(this, { childList: true });
        this.updateBalance();
        setInterval(() => this.updateBalance(), 30000);
    }

    async updateBalance() {
        try {
            const token = document.cookie.match('(^|;)\\s*jwt_token\\s*=\\s*([^;]+)')?.pop() || 
                         document.querySelector('meta[name="jwt-token"]')?.content;

            if (!token) throw new Error('Token non trovato');

            const response = await fetch('/api/teo-coins/balance/', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const data = await response.json();
            this.innerHTML = `${data.balance.toLocaleString()} TC`;
            this.style.color = 'inherit';
        } catch (error) {
            this.innerHTML = 'N/D';
            this.style.color = 'red';
        }
    }
}

customElements.define('teocoin-balance', TeoCoinBalance);