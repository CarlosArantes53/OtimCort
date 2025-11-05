// app/static/js/results.js
function imprimirPadrao(index) {
    window.print();
}

function copiarPadrao(index) {
    // Implementação simplificada
    alert('Padrão #' + index + ' copiado! (Funcionalidade completa pode ser implementada)');
}

// Animação das barras de utilização
document.addEventListener('DOMContentLoaded', function() {
    const bars = document.querySelectorAll('.visual-bar-used');
    bars.forEach((bar, index) => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = width;
        }, 100 * index);
    });
});