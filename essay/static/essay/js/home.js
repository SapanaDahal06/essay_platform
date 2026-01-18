// ===== WRITEVERSE HOMEPAGE JAVASCRIPT =====

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== STAT COUNTER ANIMATION =====
    function animateCounter(element) {
        const target = parseInt(element.getAttribute('data-target'));
        const prefix = element.getAttribute('data-prefix') || '';
        const decimal = parseInt(element.getAttribute('data-decimal')) || 0;
        const duration = 2000; // 2 seconds
        const increment = target / (duration / 16); // 60fps
        let current = 0;

        const updateCounter = () => {
            current += increment;
            if (current < target) {
                if (decimal > 0) {
                    element.textContent = prefix + current.toFixed(decimal);
                } else {
                    element.textContent = prefix + Math.floor(current).toLocaleString();
                }
                requestAnimationFrame(updateCounter);
            } else {
                if (decimal > 0) {
                    element.textContent = prefix + target.toFixed(decimal);
                } else {
                    element.textContent = prefix + target.toLocaleString();
                }
            }
        };

        updateCounter();
    }

    // Intersection Observer for stat counters
    const statNumbers = document.querySelectorAll('.stat-number');
    
    if (statNumbers.length > 0) {
        const observerOptions = {
            threshold: 0.5,
            rootMargin: '0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
                    animateCounter(entry.target);
                    entry.target.classList.add('counted');
                }
            });
        }, observerOptions);

        statNumbers.forEach(stat => observer.observe(stat));
    }

    // ===== SCROLL ANIMATIONS =====
    const observeElements = document.querySelectorAll('.step-card, .competition-card-modern, .benefit-card-modern, .leader-card');
    
    if (observeElements.length > 0) {
        const scrollObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }, index * 100); // Stagger animation
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px'
        });

        observeElements.forEach(element => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(30px)';
            element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            scrollObserver.observe(element);
        });
    }

    // ===== PROGRESS BAR ANIMATION =====
    const progressBars = document.querySelectorAll('.progress-fill');
    
    if (progressBars.length > 0) {
        const progressObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const width = entry.target.style.width;
                    entry.target.style.width = '0%';
                    setTimeout(() => {
                        entry.target.style.width = width;
                    }, 100);
                }
            });
        }, {
            threshold: 0.5
        });

        progressBars.forEach(bar => progressObserver.observe(bar));
    }

    // ===== FLOATING CARDS PARALLAX =====
    const floatingCards = document.querySelectorAll('.floating-card');
    
    if (floatingCards.length > 0 && window.innerWidth > 768) {
        window.addEventListener('mousemove', (e) => {
            const mouseX = e.clientX / window.innerWidth;
            const mouseY = e.clientY / window.innerHeight;
            
            floatingCards.forEach((card, index) => {
                const speed = (index + 1) * 0.5;
                const x = (mouseX - 0.5) * 20 * speed;
                const y = (mouseY - 0.5) * 20 * speed;
                
                card.style.transform = `translate(${x}px, ${y}px)`;
            });
        });
    }

    // ===== SMOOTH SCROLL FOR TOPIC TAGS =====
    const trendingTopics = document.querySelector('.trending-topics');
    
    if (trendingTopics && window.innerWidth <= 768) {
        let isDown = false;
        let startX;
        let scrollLeft;

        trendingTopics.addEventListener('mousedown', (e) => {
            isDown = true;
            startX = e.pageX - trendingTopics.offsetLeft;
            scrollLeft = trendingTopics.scrollLeft;
        });

        trendingTopics.addEventListener('mouseleave', () => {
            isDown = false;
        });

        trendingTopics.addEventListener('mouseup', () => {
            isDown = false;
        });

        trendingTopics.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - trendingTopics.offsetLeft;
            const walk = (x - startX) * 2;
            trendingTopics.scrollLeft = scrollLeft - walk;
        });
    }

    // ===== TOPIC TAG CLICK ANIMATION =====
    const topicTags = document.querySelectorAll('.topic-tag');
    
    topicTags.forEach(tag => {
        tag.addEventListener('click', function(e) {
            // Create ripple effect
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            ripple.style.cssText = `
                position: absolute;
                left: ${x}px;
                top: ${y}px;
                width: 0;
                height: 0;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.5);
                transform: translate(-50%, -50%);
                animation: ripple 0.6s ease-out;
                pointer-events: none;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });

    // Add ripple animation to CSS
    if (!document.querySelector('#ripple-animation')) {
        const style = document.createElement('style');
        style.id = 'ripple-animation';
        style.textContent = `
            @keyframes ripple {
                to {
                    width: 200px;
                    height: 200px;
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // ===== COMPETITION CARD HOVER EFFECT =====
    const competitionCards = document.querySelectorAll('.competition-card-modern');
    
    competitionCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.zIndex = '10';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.zIndex = '1';
        });
    });

    // ===== HERO SECTION PARALLAX =====
    const heroSection = document.querySelector('.hero-section');
    
    if (heroSection && window.innerWidth > 1024) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const heroContent = document.querySelector('.hero-content');
            const heroVisual = document.querySelector('.hero-visual');
            
            if (heroContent) {
                heroContent.style.transform = `translateY(${scrolled * 0.3}px)`;
            }
            
            if (heroVisual) {
                heroVisual.style.transform = `translateY(${scrolled * 0.15}px)`;
            }
        });
    }

    // ===== LAZY LOAD ANIMATIONS =====
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('[data-animate]');
        
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementBottom = element.getBoundingClientRect().bottom;
            
            if (elementTop < window.innerHeight && elementBottom > 0) {
                element.classList.add('animated');
            }
        });
    };

    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll(); // Run on load

    // ===== PERFORMANCE OPTIMIZATION =====
    // Debounce scroll events
    let scrollTimeout;
    window.addEventListener('scroll', () => {
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }
        scrollTimeout = setTimeout(() => {
            // Any scroll-dependent code here
        }, 100);
    });

    // ===== ACCESSIBILITY ENHANCEMENTS =====
    // Add keyboard navigation for cards
    const interactiveCards = document.querySelectorAll('.competition-card-modern, .benefit-card-modern, .leader-card');
    
    interactiveCards.forEach(card => {
        card.setAttribute('tabindex', '0');
        
        card.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                const link = this.querySelector('a');
                if (link) {
                    link.click();
                }
            }
        });
    });

    // ===== CONSOLE MESSAGE =====
    console.log('%c🚀 WriteVerse', 'font-size: 20px; font-weight: bold; color: #2563eb;');
    console.log('%cWhere writers compete, grow, and succeed!', 'font-size: 14px; color: #10b981;');
});

// ===== UTILITY FUNCTIONS =====
// Throttle function for performance
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Debounce function for performance
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}
