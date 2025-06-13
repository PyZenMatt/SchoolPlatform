// TeoArt School Platform Documentation Site JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add scroll effect to navbar
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.site-header');
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    // Observe feature cards and tech items
    document.querySelectorAll('.feature-card, .tech-item').forEach(el => {
        observer.observe(el);
    });

    // Copy to clipboard functionality
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const target = document.querySelector(this.getAttribute('data-target'));
            if (target) {
                navigator.clipboard.writeText(target.textContent).then(() => {
                    this.textContent = 'Copiato!';
                    setTimeout(() => {
                        this.textContent = 'Copia';
                    }, 2000);
                });
            }
        });
    });

    // Form validation and submission
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Basic validation
            const name = this.querySelector('input[name="name"]').value;
            const email = this.querySelector('input[name="email"]').value;
            const message = this.querySelector('textarea[name="message"]').value;
            
            if (!name || !email || !message) {
                alert('Per favore compila tutti i campi richiesti.');
                return;
            }
            
            if (!isValidEmail(email)) {
                alert('Per favore inserisci un indirizzo email valido.');
                return;
            }
            
            // Simulate form submission
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Invio in corso...';
            submitBtn.disabled = true;
            
            setTimeout(() => {
                alert('Messaggio inviato con successo!');
                this.reset();
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }, 2000);
        });
    }

    // Demo modal functionality
    const demoButtons = document.querySelectorAll('.demo-btn');
    demoButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const demoType = this.getAttribute('data-demo');
            showDemoModal(demoType);
        });
    });

    // Tech stack hover effects
    document.querySelectorAll('.tech-item').forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.05)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
});

// Utility functions
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function showDemoModal(demoType) {
    // Create modal dynamically
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Demo: ${demoType}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="demo-content">
                        <p>Demo della funzionalità: <strong>${demoType}</strong></p>
                        <div class="demo-placeholder">
                            <i class="fas fa-play-circle fa-3x text-primary"></i>
                            <p>Demo interattiva disponibile nella versione live della piattaforma</p>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Chiudi</button>
                    <a href="/contact/" class="btn btn-primary">Richiedi Accesso</a>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Remove modal from DOM after hide
    modal.addEventListener('hidden.bs.modal', function() {
        modal.remove();
    });
}

// Parallax effect for hero section
window.addEventListener('scroll', function() {
    const scrolled = window.pageYOffset;
    const heroImage = document.querySelector('.hero-image');
    if (heroImage) {
        heroImage.style.transform = `translateY(${scrolled * 0.5}px)`;
    }
});

// Add CSS for scrolled navbar
const style = document.createElement('style');
style.textContent = `
    .site-header.scrolled {
        background: rgba(0, 123, 255, 0.95);
        backdrop-filter: blur(10px);
    }
    
    .animate-in {
        animation: slideInUp 0.6s ease-out;
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .demo-placeholder {
        text-align: center;
        padding: 40px;
        background: #f8f9fa;
        border-radius: 10px;
        margin: 20px 0;
    }
`;
document.head.appendChild(style);
