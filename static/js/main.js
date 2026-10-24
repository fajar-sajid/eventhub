document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseInt(el.dataset.count);
    let cur = 0;
    const step = Math.max(1, Math.ceil(target / 60));
    const timer = setInterval(() => {
        cur += step;
        if (cur >= target) { cur = target; clearInterval(timer); }
        el.textContent = cur + '+';
    }, 25);
});

const liveSearch = document.getElementById('liveSearch');
if (liveSearch) {
    liveSearch.addEventListener('input', e => {
        const q = e.target.value.toLowerCase();
        document.querySelectorAll('.event-card').forEach(card => {
            const text = card.dataset.search || card.textContent.toLowerCase();
            card.parentElement.style.display = text.includes(q) ? '' : 'none';
        });
    });
}

document.querySelectorAll('.tilt').forEach(card => {
    card.addEventListener('mousemove', e => {
        const r = card.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - .5;
        const y = (e.clientY - r.top) / r.height - .5;
        card.style.transform = `perspective(900px) rotateY(${x*8}deg) rotateX(${-y*8}deg) translateY(-8px)`;
    });
    card.addEventListener('mouseleave', () => card.style.transform = '');
});

setTimeout(() => {
    document.querySelectorAll('.alert').forEach(a => {
        if (window.bootstrap) new bootstrap.Alert(a).close();
    });
}, 5000);