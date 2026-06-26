// ============================================
// ANIMACIONES.JS - Animaciones y efectos visuales
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar partículas
    initParticles();
    
    // Inicializar contadores animados
    initCounters();
    
    // Inicializar hover effects
    initHoverEffects();
});

// ============================================
// PARTÍCULAS DE FONDO
// ============================================
function initParticles() {
    const container = document.querySelector('.particles');
    if (!container) return;
    
    const particleCount = 50;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        const size = Math.random() * 4 + 2;
        const x = Math.random() * 100;
        const y = Math.random() * 100;
        const duration = Math.random() * 20 + 15;
        const delay = Math.random() * 10;
        
        particle.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            left: ${x}%;
            top: ${y}%;
            animation-duration: ${duration}s;
            animation-delay: ${delay}s;
            opacity: ${Math.random() * 0.5 + 0.2};
        `;
        
        container.appendChild(particle);
    }
}

// ============================================
// CONTADORES ANIMADOS
// ============================================
function initCounters() {
    const counters = document.querySelectorAll('.stat-number');
    
    counters.forEach(counter => {
        const target = parseInt(counter.textContent);
        if (isNaN(target)) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(counter, target);
                    observer.unobserve(counter);
                }
            });
        });
        
        observer.observe(counter);
    });
}

function animateCounter(element, target) {
    let current = 0;
    const duration = 2000;
    const steps = 60;
    const increment = target / steps;
    const interval = duration / steps;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, interval);
}

// ============================================
// HOVER EFFECTS
// ============================================
function initHoverEffects() {
    // Efecto de zoom en imágenes de productos
    document.querySelectorAll('.product-image img').forEach(img => {
        img.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
        });
        img.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // Efecto de elevación en tarjetas
    document.querySelectorAll('.product-card, .business-card, .category-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
            this.style.boxShadow = '0 20px 40px rgba(0,0,0,0.1)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
        });
    });
}