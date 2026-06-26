// ============================================
// DASHBOARD.JS - Panel de control del vendedor
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar gráficas si existen
    if (document.getElementById('salesChart')) {
        initCharts();
    }
});

// ============================================
// GRÁFICAS CON CHART.JS
// ============================================
function initCharts() {
    // Cargar Chart.js desde CDN
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
    script.onload = function() {
        createSalesChart();
        createTopProductsChart();
    };
    document.head.appendChild(script);
}

function createSalesChart() {
    const ctx = document.getElementById('salesChart');
    if (!ctx) return;
    
    // Datos de ejemplo - en producción se cargarían desde la API
    const data = {
        labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
        datasets: [{
            label: 'Ventas (Bs)',
            data: [1200, 1900, 1500, 2200, 2800, 3100],
            backgroundColor: 'rgba(16, 185, 129, 0.2)',
            borderColor: '#10B981',
            borderWidth: 3,
            tension: 0.4,
            fill: true
        }]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'Bs ' + value;
                        }
                    }
                }
            }
        }
    });
}

function createTopProductsChart() {
    const ctx = document.getElementById('topProductsChart');
    if (!ctx) return;
    
    // Datos de ejemplo
    const data = {
        labels: ['Producto A', 'Producto B', 'Producto C', 'Producto D', 'Producto E'],
        datasets: [{
            label: 'Unidades Vendidas',
            data: [45, 38, 25, 18, 12],
            backgroundColor: ['#10B981', '#34D399', '#6EE7B7', '#A7F3D0', '#D1FAE5'],
            borderColor: '#059669',
            borderWidth: 1
        }]
    };
    
    new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// ============================================
// EXPORTAR DATOS
// ============================================
function exportData(type) {
    fetch(`/api/export/${type}`)
        .then(res => res.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `reporte_${type}_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
        });
}