// Modern SchoolPlatform JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS (Animate On Scroll)
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-in-out',
            once: true
        });
    }

    // Smooth scrolling for navigation links
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

    // Navbar scroll effect
    const navbar = document.querySelector('.modern-navbar');
    let lastScrollY = window.scrollY;

    window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;
        
        if (currentScrollY > 100) {
            navbar.style.background = 'rgba(26, 26, 26, 0.98)';
            navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
        } else {
            navbar.style.background = 'rgba(26, 26, 26, 0.95)';
            navbar.style.boxShadow = 'none';
        }

        // Hide/show navbar on scroll
        if (currentScrollY > lastScrollY && currentScrollY > 200) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }
        
        lastScrollY = currentScrollY;
    });

    // Counter animation for stats
    function animateCounter(element, target, duration = 2000) {
        let start = 0;
        const startTime = performance.now();
        
        function updateCounter(currentTime) {
            const elapsedTime = currentTime - startTime;
            const progress = Math.min(elapsedTime / duration, 1);
            
            // Easing function for smooth animation
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(start + (target - start) * easeOut);
            
            element.textContent = current + '+';
            
            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = target + '+';
            }
        }
        
        requestAnimationFrame(updateCounter);
    }

    // Trigger counter animation when stats come into view
    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px 0px -100px 0px'
    };

    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const statNumbers = entry.target.querySelectorAll('.stat-number');
                statNumbers.forEach(stat => {
                    const text = stat.textContent;
                    const number = parseInt(text.replace(/\D/g, ''));
                    if (number && !stat.hasAttribute('data-animated')) {
                        stat.setAttribute('data-animated', 'true');
                        animateCounter(stat, number);
                    }
                });
            }
        });
    }, observerOptions);

    const heroStats = document.querySelector('.hero-stats');
    if (heroStats) {
        statsObserver.observe(heroStats);
    }

    // Add loading animation to buttons
    document.querySelectorAll('.btn-modern').forEach(button => {
        button.addEventListener('click', function(e) {
            if (this.href && !this.href.startsWith('#')) {
                // Add loading effect for external links
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Caricamento...';
                
                setTimeout(() => {
                    this.innerHTML = originalText;
                }, 1000);
            }
        });
    });

    // Add some interactive particles
    function createParticle(x, y) {
        const particle = document.createElement('div');
        particle.style.position = 'fixed';
        particle.style.left = x + 'px';
        particle.style.top = y + 'px';
        particle.style.width = '4px';
        particle.style.height = '4px';
        particle.style.background = '#4facfe';
        particle.style.borderRadius = '50%';
        particle.style.pointerEvents = 'none';
        particle.style.zIndex = '9999';
        particle.style.animation = 'particleFloat 1s ease-out forwards';
        
        document.body.appendChild(particle);
        
        setTimeout(() => {
            particle.remove();
        }, 1000);
    }

    // Add CSS animation for particles
    const style = document.createElement('style');
    style.textContent = `
        @keyframes particleFloat {
            0% {
                transform: translateY(0) scale(1);
                opacity: 1;
            }
            100% {
                transform: translateY(-100px) scale(0);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);

    // Console Easter Egg
    console.log(`
    🎓 SchoolPlatform Developer Tools
    
    Sei interessato alla tecnologia dietro la piattaforma?
    Dai un'occhiata al nostro GitHub: https://github.com/yourusername
    
    Stack tecnologico:
    • Frontend: React.js
    • Backend: Django
    • Blockchain: Polygon (TeoCoin ERC-20)
    • Database: PostgreSQL
    • Deployment: Docker + AWS
    
    Contributi e feedback sono sempre benvenuti!
    `);

    // FAQ Toggle Functionality
    function initFAQ() {
        const faqItems = document.querySelectorAll('.faq-item');
        
        faqItems.forEach(item => {
            const question = item.querySelector('.faq-question');
            const answer = item.querySelector('.faq-answer');
            const icon = item.querySelector('.faq-icon');
            
            if (question && answer) {
                question.addEventListener('click', () => {
                    const isActive = item.classList.contains('active');
                    
                    // Close all other FAQ items
                    faqItems.forEach(otherItem => {
                        if (otherItem !== item) {
                            otherItem.classList.remove('active');
                            const otherQuestion = otherItem.querySelector('.faq-question');
                            const otherAnswer = otherItem.querySelector('.faq-answer');
                            if (otherQuestion) otherQuestion.classList.remove('active');
                            if (otherAnswer) otherAnswer.classList.remove('open');
                        }
                    });
                    
                    // Toggle current item
                    const newActiveState = !isActive;
                    item.classList.toggle('active', newActiveState);
                    question.classList.toggle('active', newActiveState);
                    answer.classList.toggle('open', newActiveState);
                });
            }
        });
    }

    // ========================================
    // PREMIUM FAQ FUNCTIONALITY
    // ========================================
  
    // Initialize FAQ functionality
    function initPremiumFAQ() {
        // Category switching
        const categoryBtns = document.querySelectorAll('.faq-category-btn');
        const categoryContents = document.querySelectorAll('.faq-category-content');
        
        categoryBtns.forEach(btn => {
          btn.addEventListener('click', () => {
            const targetCategory = btn.getAttribute('data-category');
            
            // Update active button
            categoryBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show target content
            categoryContents.forEach(content => {
              content.classList.remove('active');
              if (content.id === targetCategory) {
                content.classList.add('active');
                
                // Re-trigger AOS animations for newly visible content
                setTimeout(() => {
                  if (typeof AOS !== 'undefined') {
                    AOS.refresh();
                  }
                }, 100);
              }
            });
          });
        });
        
        // FAQ card expand/collapse
        const faqCards = document.querySelectorAll('.premium-faq-card');
        
        faqCards.forEach(card => {
          const header = card.querySelector('.faq-card-header');
          const content = card.querySelector('.faq-card-content');
          const expandIcon = card.querySelector('.faq-expand');
          
          header.addEventListener('click', () => {
            const isOpen = content.classList.contains('active');
            
            // Close all other cards in the same category
            const currentCategory = card.closest('.faq-category-content');
            const otherCards = currentCategory.querySelectorAll('.premium-faq-card');
            otherCards.forEach(otherCard => {
              if (otherCard !== card) {
                otherCard.querySelector('.faq-card-content').classList.remove('active');
                otherCard.querySelector('.faq-card-header').classList.remove('active');
              }
            });
            
            // Toggle current card
            if (isOpen) {
              content.classList.remove('active');
              header.classList.remove('active');
            } else {
              content.classList.add('active');
              header.classList.add('active');
              
              // Smooth scroll to card if needed
              setTimeout(() => {
                const headerOffset = 100;
                const elementPosition = card.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                
                if (elementPosition < 0) {
                  window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                  });
                }
              }, 300);
            }
          });
        });
      }
      
      // FAQ Stats Counter Animation
      function animateFAQStats() {
        const stats = document.querySelectorAll('.faq-stat .stat-number');
        
        const animateValue = (element, start, end, duration) => {
          const range = end - start;
          const increment = range / (duration / 16);
          let current = start;
          
          const timer = setInterval(() => {
            current += increment;
            
            if (current >= end) {
              element.textContent = formatStatNumber(end);
              clearInterval(timer);
            } else {
              element.textContent = formatStatNumber(Math.floor(current));
            }
          }, 16);
        };
        
        const formatStatNumber = (num) => {
          const text = num.toString();
          if (text.includes('€')) return text;
          if (text.includes('%')) return text;
          if (text.includes('mesi')) return text;
          return text;
        };
        
        // Intersection Observer for stats animation
        const statsObserver = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const statElement = entry.target;
              const originalText = statElement.textContent;
              
              // Extract number for animation
              if (originalText.includes('€400B+')) {
                animateValue(statElement, 0, 400, 2000);
                setTimeout(() => statElement.textContent = '€400B+', 2000);
              } else if (originalText.includes('18 mesi')) {
                animateValue(statElement, 0, 18, 1500);
                setTimeout(() => statElement.textContent = '18 mesi', 1500);
              } else if (originalText.includes('100%')) {
                animateValue(statElement, 0, 100, 1800);
                setTimeout(() => statElement.textContent = '100%', 1800);
              }
              
              statsObserver.unobserve(statElement);
            }
          });
        }, { threshold: 0.5 });
        
        stats.forEach(stat => statsObserver.observe(stat));
      }
      
      // FAQ Search Functionality
      function initFAQSearch() {
        // Add search box if it doesn't exist
        const faqHeader = document.querySelector('.faq-header');
        if (faqHeader && !faqHeader.querySelector('.faq-search')) {
          const searchBox = document.createElement('div');
          searchBox.className = 'faq-search';
          searchBox.innerHTML = `
            <input type="text" placeholder="Cerca nelle FAQ..." class="faq-search-input">
            <span class="faq-search-icon">🔍</span>
          `;
          faqHeader.appendChild(searchBox);
          
          const searchInput = searchBox.querySelector('.faq-search-input');
          searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const allCards = document.querySelectorAll('.premium-faq-card');
            
            allCards.forEach(card => {
              const question = card.querySelector('h3').textContent.toLowerCase();
              const content = card.querySelector('.faq-card-content').textContent.toLowerCase();
              
              if (question.includes(searchTerm) || content.includes(searchTerm)) {
                card.style.display = 'block';
              } else {
                card.style.display = searchTerm ? 'none' : 'block';
              }
            });
          });
        }
      }
  
    // Call FAQ init on page load
    initFAQ();
    // Initialize Premium FAQ when DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            if (document.querySelector('.premium-faq-section')) {
                initPremiumFAQ();
                animateFAQStats();
                initFAQSearch();
            }
        });
    } else {
        if (document.querySelector('.premium-faq-section')) {
            initPremiumFAQ();
            animateFAQStats();
            initFAQSearch();
        }
    }

    // Mobile Menu Toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');
    const mobileNavLinks = document.querySelectorAll('.mobile-nav-link');
    
    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            mobileMenu.classList.toggle('active');
            mobileMenuToggle.classList.toggle('active');
            
            // Prevent body scroll when menu is open
            if (mobileMenu.classList.contains('active')) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        });
        
        // Close menu when clicking on links
        mobileNavLinks.forEach(link => {
            link.addEventListener('click', function() {
                mobileMenu.classList.remove('active');
                mobileMenuToggle.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!mobileMenu.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
                mobileMenu.classList.remove('active');
                mobileMenuToggle.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
        
        // Close menu on window resize if mobile menu is open
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                mobileMenu.classList.remove('active');
                mobileMenuToggle.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }
    
    // FAQ Tab Navigation Functionality
    function initFAQTabs() {
        const tabs = document.querySelectorAll('.faq-tab');
        const sections = document.querySelectorAll('.faq-section-content');
        
        if (tabs.length === 0 || sections.length === 0) return;
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetSection = tab.getAttribute('data-section');
                
                // Remove active class from all tabs and sections
                tabs.forEach(t => t.classList.remove('active'));
                sections.forEach(s => s.classList.remove('active'));
                
                // Add active class to clicked tab
                tab.classList.add('active');
                
                // Show target section
                const targetContent = document.getElementById(`${targetSection}-section`);
                if (targetContent) {
                    targetContent.classList.add('active');
                    
                    // Re-trigger AOS animations for newly visible content
                    setTimeout(() => {
                        if (typeof AOS !== 'undefined') {
                            AOS.refresh();
                        }
                    }, 100);
                }
                
                // Add subtle scroll to section if needed
                const comprehensiveSection = document.querySelector('.faq-comprehensive-section');
                if (comprehensiveSection) {
                    const headerOffset = 120;
                    const elementPosition = comprehensiveSection.getBoundingClientRect().top;
                    
                    if (elementPosition < -200) {
                        setTimeout(() => {
                            const offsetPosition = comprehensiveSection.offsetTop - headerOffset;
                            window.scrollTo({
                                top: offsetPosition,
                                behavior: 'smooth'
                            });
                        }, 150);
                    }
                }
            });
        });
        
        // Initialize with first tab active
        if (tabs.length > 0 && !document.querySelector('.faq-tab.active')) {
            tabs[0].click();
        }
    }

    // Initialize FAQ Tabs
    initFAQTabs();
});
