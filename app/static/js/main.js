// ============================================
// MAIN.JS - Funcionalidades globales
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar dropdowns
    initDropdowns();
    
    // Inicializar búsqueda en tiempo real
    initSearch();
    
    // Inicializar notificaciones
    initNotifications();
});

// ============================================
// DROPDOWNS
// ============================================
function initDropdowns() {
    document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.stopPropagation();
            const menu = this.nextElementSibling;
            menu.classList.toggle('show');
        });
    });
    
    // Cerrar dropdowns al hacer clic fuera
    document.addEventListener('click', function() {
        document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
            menu.classList.remove('show');
        });
    });
}

// ============================================
// BÚSQUEDA EN TIEMPO REAL (Página principal)
// ============================================
function initSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const query = this.value.toLowerCase().trim();
        const cards = document.querySelectorAll('.business-card, .product-card');
        
        cards.forEach(card => {
            const text = card.textContent.toLowerCase();
            card.style.display = text.includes(query) ? '' : 'none';
        });
    });
}

// ============================================
// NOTIFICACIONES EN TIEMPO REAL
// ============================================
function initNotifications() {
    // Verificar notificaciones no leídas cada 30 segundos
    setInterval(checkNotifications, 30000);
}

function checkNotifications() {
    if (!document.querySelector('.notification-badge')) return;
    
    fetch('/api/notifications/unread')
        .then(res => res.json())
        .then(data => {
            const badge = document.querySelector('.notification-badge');
            if (data.count > 0) {
                badge.textContent = data.count;
                badge.style.display = 'block';
            } else {
                badge.style.display = 'none';
            }
        });
}

// ============================================
// UTILIDADES
// ============================================
function formatPrice(price) {
    return 'Bs ' + parseFloat(price).toFixed(2);
}

function truncateText(text, length = 100) {
    if (text.length <= length) return text;
    return text.substring(0, length) + '...';
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}