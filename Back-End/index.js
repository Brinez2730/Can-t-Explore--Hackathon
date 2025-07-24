// Abrir/Fechar Menu
const botaoMore = document.getElementById('more');
const menuLateral = document.getElementById('menu-lateral');
const botaoFechar = document.getElementById('fechar-menu');

botaoMore.addEventListener('click', () => {
    menuLateral.classList.add('menu-ativo');
});

botaoFechar.addEventListener('click', () => {
    menuLateral.classList.remove('menu-ativo');
});

// Fechar ao clicar fora do menu
document.addEventListener('click', (e) => {
    if (!menuLateral.contains(e.target) && e.target.id !== 'more') {
        menuLateral.classList.remove('menu-ativo');
    }
});