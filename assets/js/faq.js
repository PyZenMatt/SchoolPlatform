document.addEventListener('DOMContentLoaded', function() {
    // FAQ Tab switching
    const faqTabs = document.querySelectorAll('.faq-tab');
    const faqSections = document.querySelectorAll('.faq-section-content');
    
    faqTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetSection = this.getAttribute('data-section');
            
            // Remove active class from all tabs and sections
            faqTabs.forEach(t => t.classList.remove('active'));
            faqSections.forEach(s => s.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding section
            this.classList.add('active');
            const targetElement = document.getElementById(targetSection + '-section');
            if (targetElement) {
                targetElement.classList.add('active');
            }
        });
    });
    
    // FAQ Accordion functionality
    const faqQuestions = document.querySelectorAll('.faq-accordion h4');
    
    faqQuestions.forEach(question => {
        question.addEventListener('click', function() {
            const answer = this.nextElementSibling;
            const isOpen = answer.classList.contains('open');
            
            // Close all other answers
            document.querySelectorAll('.faq-accordion p').forEach(p => {
                p.classList.remove('open');
            });
            document.querySelectorAll('.faq-accordion h4').forEach(q => {
                q.classList.remove('active');
            });
            
            // Toggle current answer
            if (!isOpen) {
                answer.classList.add('open');
                this.classList.add('active');
            }
        });
    });
    
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
    
    // Initialize AOS if available
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 600,
            easing: 'ease-out-cubic',
            once: true,
            offset: 50
        });
    }
    
    // Add glassmorphism effect on scroll
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.modern-navbar');
        if (navbar) {
            if (window.scrollY > 100) {
                navbar.style.background = 'rgba(26, 26, 26, 0.98)';
                navbar.style.backdropFilter = 'blur(25px)';
            } else {
                navbar.style.background = 'rgba(26, 26, 26, 0.95)';
                navbar.style.backdropFilter = 'blur(20px)';
            }
        }
    });
});
