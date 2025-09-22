document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('toggleContext');
    const panel = document.getElementById('contextPanel');
    if (toggle && panel) {
        toggle.addEventListener('change', () => {
            panel.style.display = toggle.checked ? 'block' : 'none';
        });
    }
});