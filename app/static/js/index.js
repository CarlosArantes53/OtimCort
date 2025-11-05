// app/static/js/index.js
function otimizar(itemCode) {
    window.location.href = '/otimizar/' + itemCode;
}

function atualizarLargura() {
    const largura = document.getElementById('larguraChapa').value;
    
    fetch('/api/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ largura_chapa: parseFloat(largura) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Largura da chapa atualizada para ' + data.largura_chapa + 'mm');
            location.reload();
        } else {
            alert('Erro ao atualizar largura');
        }
    });
}

function filtrarItens() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const cards = document.querySelectorAll('.item-card');
    
    cards.forEach(card => {
        const searchData = card.getAttribute('data-search');
        if (searchData.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}