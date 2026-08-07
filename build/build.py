# -*- coding: utf-8 -*-
"""
Сборщик посадочных страниц по направлениям для «Твоя Сцена».

Как пользоваться:
    python3 build/build.py

Что делает:
  - берёт тексты из build/directions.json
  - берёт CSS из index.html (чтобы стили главной и посадочных не расходились)
  - подставляет всё в build/template.html
  - кладёт результат в /гитара/index.html, /вокал/index.html и т.д.
  - пересобирает sitemap.xml

Правки текстов — только в build/directions.json. Правки вёрстки — в build/template.html.
Руками файлы в папках направлений не редактируем: они перезаписываются при сборке.
"""
import io, json, os, re, html, datetime
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, 'build')
SITE = 'https://tvoyascena.ru'
YM_ID = 111352709
ALL_VIDEOS = ['v%d' % i for i in range(1, 13)]


def read(p):
    return io.open(p, encoding='utf-8').read()


def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, 'w', encoding='utf-8').write(s)


# ---------- CSS главной страницы ----------
index_html = read(os.path.join(ROOT, 'index.html'))
m = re.search(r'<style>(.*?)</style>', index_html, re.S)
if not m:
    raise SystemExit('Не нашёл <style> в index.html')
BASE_CSS = m.group(1)

EXTRA_CSS = """
        /* ===== ДОБАВЛЕНО ДЛЯ ПОСАДОЧНЫХ ПО НАПРАВЛЕНИЯМ ===== */
        nav { gap: 28px; }
        .nav-links { gap: 22px; flex: 0 1 auto; }
        .nav-phone { color: var(--yellow); text-decoration: none; font-weight: 800; font-size: 0.95rem; letter-spacing: 0.5px; white-space: nowrap; }
        .nav-phone:hover { color: var(--yellow-hover); }
        @media (max-width: 1200px) { .nav-links a { font-size: 0.78rem; } .nav-links { gap: 16px; } }

        /* Строка фактов на первом экране */
        .facts-bar { display: flex; flex-wrap: wrap; justify-content: center; gap: 0; max-width: 900px; margin: 0 auto 30px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); }
        .facts-bar .fact { flex: 1 1 200px; display: flex; flex-direction: column; gap: 5px; padding: 16px 20px; border-right: 1px solid rgba(255,255,255,0.06); text-align: left; }
        .facts-bar .fact:last-child { border-right: none; }
        .fact-k { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 1.5px; color: var(--gray); font-weight: 700; }
        .fact-v { font-size: 0.92rem; font-weight: 700; color: var(--white); text-decoration: none; }
        a.fact-v:hover { color: var(--yellow); }

        /* Таймлайн результата */
        .timeline-section { padding: 100px 40px; background: var(--dark); position: relative; z-index: 2; }
        .timeline { max-width: 900px; margin: 0 auto; display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
        .tl-item { background: var(--black); border: 1px solid rgba(255,255,255,0.06); padding: 32px 28px; position: relative; transition: border-color 0.3s; }
        .tl-item:hover { border-color: rgba(255,214,0,0.3); }
        .tl-item::before { content: ''; position: absolute; top: 0; left: 0; width: 40px; height: 3px; background: var(--yellow); }
        .tl-when { font-size: 1.1rem; font-weight: 900; color: var(--yellow); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 14px; }
        .tl-what { font-size: 0.92rem; color: var(--light-gray); line-height: 1.65; }
        .timeline-cta { text-align: center; margin-top: 44px; }

        /* FAQ */
        .faq-section { padding: 100px 40px; position: relative; z-index: 2; }
        .faq-list { max-width: 820px; margin: 0 auto; }
        .faq-item { border-bottom: 1px solid rgba(255,255,255,0.08); }
        .faq-q { width: 100%; background: none; border: none; color: var(--white); font-family: 'Montserrat', sans-serif; font-size: 1rem; font-weight: 700; text-align: left; padding: 24px 44px 24px 0; cursor: pointer; position: relative; line-height: 1.45; }
        .faq-q::after { content: '+'; position: absolute; right: 8px; top: 50%; transform: translateY(-50%); font-size: 1.6rem; font-weight: 400; color: var(--yellow); transition: transform 0.3s; }
        .faq-item.open .faq-q::after { transform: translateY(-50%) rotate(45deg); }
        .faq-q:hover { color: var(--yellow); }
        .faq-a { max-height: 0; overflow: hidden; transition: max-height 0.35s ease; }
        .faq-a p { color: var(--light-gray); font-size: 0.93rem; line-height: 1.75; padding: 0 44px 26px 0; }

        /* Тарифы */
        .prices { padding: 100px 40px; background: var(--dark); position: relative; z-index: 2; }
        .prices-grid { max-width: 900px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; }
        .price-card { background: var(--black); border: 1px solid rgba(255,255,255,0.08); padding: 36px 28px; text-align: center; }
        .price-card.featured { border-color: var(--yellow); }
        .price-name { font-size: 0.95rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 14px; }
        .price-value { font-size: 2.1rem; font-weight: 900; color: var(--yellow); margin-bottom: 8px; }
        .price-note { font-size: 0.82rem; color: var(--gray); line-height: 1.6; }

        /* Другие направления */
        .other-dirs { padding: 90px 40px; position: relative; z-index: 2; }
        .other-dirs-grid { max-width: 1100px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; }
        .other-dir { display: flex; align-items: center; gap: 12px; background: var(--dark-card); border: 1px solid rgba(255,255,255,0.06); padding: 20px 22px; text-decoration: none; color: var(--white); font-weight: 700; font-size: 0.95rem; transition: all 0.3s; }
        .other-dir:hover { border-color: rgba(255,214,0,0.4); transform: translateY(-2px); }
        .other-dir .od-icon { font-size: 1.5rem; }


        /* ===== ПЕРВЫЙ ЭКРАН С ФОРМОЙ ===== */
        .hero-split { min-height: auto; padding: 130px 40px 80px; display: block; position: relative; overflow: hidden; }
        .hero-bg { position: absolute; inset: 0; background-size: cover; background-position: center 35%; opacity: 0.30; z-index: 0; }
        .hero-split::after { content: ''; position: absolute; inset: 0; z-index: 1;
            background: linear-gradient(90deg, rgba(10,10,10,0.94) 0%, rgba(10,10,10,0.80) 45%, rgba(10,10,10,0.92) 100%); }
        .hero-grid { position: relative; z-index: 3; max-width: 1240px; margin: 0 auto;
            display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 50px; align-items: center; text-align: left; }
        .hero-left { max-width: none; }
        .hero-split h1 { font-size: clamp(2rem, 3.6vw, 3.4rem); text-align: left; margin-bottom: 20px; }
        .hero-split .hero-content, .hero-split p { text-align: left; margin-left: 0; }
        .hero-split .hero-badge { margin-bottom: 22px; }
        .hero-split .facts-bar { margin: 26px 0 18px; max-width: none; }
        .hero-split .hero-micro-proof { margin-top: 4px; }

        .hero-form { background: rgba(20,20,20,0.94); border: 1px solid rgba(255,214,0,0.28); padding: 34px 30px;
            box-shadow: 0 24px 60px rgba(0,0,0,0.55); }
        .hero-form h2 { font-size: 1.35rem; font-weight: 900; text-transform: uppercase; margin-bottom: 8px; line-height: 1.25; }
        .hero-form h2 span { color: var(--yellow); }
        .hf-sub { color: var(--gray); font-size: 0.85rem; line-height: 1.55; margin-bottom: 20px; }
        .hero-form .cta-form { max-width: none; gap: 12px; }
        .hero-form .cta-form input, .hero-form .cta-form select { padding: 15px 18px; font-size: 0.9rem; }
        .hero-form .btn-primary { padding: 17px; font-size: 0.95rem; }
        .hero-form .cta-spots { font-size: 0.78rem; }
        .hf-alt { margin-top: 16px; font-size: 0.82rem; color: var(--gray); text-align: center; }
        .hf-alt a { color: var(--yellow); font-weight: 700; text-decoration: none; }

        /* ===== ГАЛЕРЕЯ ===== */
        .gallery { padding: 100px 40px; position: relative; z-index: 2; }
        .gallery-grid { max-width: 1180px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 16px; }
        .gallery-grid img { width: 100%; height: 100%; aspect-ratio: 4/5; object-fit: cover; display: block;
            border: 1px solid rgba(255,255,255,0.07); transition: transform 0.4s, border-color 0.3s; }
        .gallery-grid img:hover { transform: translateY(-4px); border-color: rgba(255,214,0,0.4); }

        /* ===== ГДЕ МЫ ЗАНИМАЕМСЯ ===== */
        .place { padding: 100px 40px; background: var(--dark); position: relative; z-index: 2; }
        /* кладка: каждое фото сохраняет свои пропорции, класс видно целиком */
        .place-grid { max-width: 1180px; margin: 0 auto; column-count: 3; column-gap: 16px; }
        .place-grid img { width: 100%; height: auto; display: block; margin-bottom: 16px;
            break-inside: avoid; -webkit-column-break-inside: avoid; border: 1px solid rgba(255,255,255,0.07);
            transition: border-color 0.3s; }
        .place-grid img:hover { border-color: rgba(255,214,0,0.35); }
        @media (max-width: 900px) { .place-grid { column-count: 2; } }
        @media (max-width: 560px) { .place-grid { column-count: 1; } }
        .place-cta { text-align: center; margin-top: 40px; display: flex; gap: 26px; justify-content: center; align-items: center; flex-wrap: wrap; }
        .place-map { color: var(--yellow); font-weight: 700; text-decoration: none; font-size: 0.9rem; }

        @media (max-width: 980px) {
            .hero-grid { grid-template-columns: 1fr; gap: 34px; }
            .hero-split { padding: 105px 20px 60px; }
            .hero-split h1 { font-size: clamp(1.8rem, 7vw, 2.6rem); }
            .hero-form { padding: 26px 20px; }
            .gallery, .place { padding: 70px 20px; }
        }
        @media (max-width: 900px) {
            .timeline { grid-template-columns: 1fr; }
        }
        @media (max-width: 768px) {
            .nav-phone { display: none; }
            .facts-bar { flex-direction: column; }
            .facts-bar .fact { border-right: none; border-bottom: 1px solid rgba(255,255,255,0.06); text-align: center; align-items: center; }
            .facts-bar .fact:last-child { border-bottom: none; }
            .timeline-section, .faq-section, .prices, .other-dirs { padding: 70px 20px; }
        }
"""

JS = """
        // ===== БУРГЕР =====
        document.getElementById('burger').addEventListener('click', () => {
            document.getElementById('navLinks').classList.toggle('active');
        });
        document.querySelectorAll('.nav-links a').forEach(l => {
            l.addEventListener('click', () => document.getElementById('navLinks').classList.remove('active'));
        });

        // ===== ИСТОЧНИК ТРАФИКА =====
        const TRAFFIC_KEYS = ['utm_source','utm_medium','utm_campaign','utm_content','utm_term','yclid'];
        const traffic = (function () {
            const url = new URLSearchParams(location.search);
            let saved = {};
            try { saved = JSON.parse(sessionStorage.getItem('ts_traffic') || '{}'); } catch (e) {}
            let touched = false;
            TRAFFIC_KEYS.forEach(k => { const v = url.get(k); if (v) { saved[k] = v.slice(0,200); touched = true; } });
            if (touched || !saved.first_landing) {
                saved.first_landing = saved.first_landing || location.href.slice(0,500);
                saved.referrer = saved.referrer || document.referrer.slice(0,300);
                try { sessionStorage.setItem('ts_traffic', JSON.stringify(saved)); } catch (e) {}
            }
            return saved;
        })();

        // ===== ЖИВОЙ ДЕДЛАЙН =====
        (function () {
            const M = ['январь','февраль','март','апрель','май','июнь','июль','август','сентябрь','октябрь','ноябрь','декабрь'];
            const el = document.getElementById('heroMonth');
            if (!el) return;
            const now = new Date();
            el.textContent = M[now.getDate() > 25 ? (now.getMonth() + 1) % 12 : now.getMonth()];
        })();

        // ===== (маска телефона перенесена в обработчик форм) =====
        (function () {
            const input = null; if (!input) return;
            const _unused = document.querySelector('.cta-form input[name="phone"]');
            if (!input) return;
            input.setAttribute('inputmode','tel');
            input.placeholder = '+7 (___) ___-__-__';
            function fmt(v) {
                let d = v.replace(/\\D/g,'');
                if (d.startsWith('8')) d = '7' + d.slice(1);
                if (!d.startsWith('7')) d = '7' + d;
                d = d.slice(0,11);
                let o = '+7';
                if (d.length > 1) o += ' (' + d.slice(1,4);
                if (d.length >= 4) o += ')';
                if (d.length > 4) o += ' ' + d.slice(4,7);
                if (d.length > 7) o += '-' + d.slice(7,9);
                if (d.length > 9) o += '-' + d.slice(9,11);
                return o;
            }
            input.addEventListener('input', () => { input.value = fmt(input.value); });
            input.addEventListener('focus', () => { if (!input.value) input.value = '+7 ('; });
        })();

        // ===== ЦЕЛИ НА КЛИКАХ =====
        document.addEventListener('click', e => {
            const a = e.target.closest('a');
            if (!a) return;
            if (a.dataset.goal) { goal(a.dataset.goal); return; }
            const h = a.getAttribute('href') || '';
            if (h.startsWith('tel:')) goal('phone_click');
            else if (h.indexOf('vk.com') !== -1 || h.indexOf('vk.me') !== -1) goal('vk_click');
            else if (h === '#signup') goal('cta_click');
        });

        // ===== ФОРМЫ (их две: на первом экране и внизу) =====
        const FORM_ENDPOINT = 'https://193-29-225-72.sslip.io:8788';

        document.querySelectorAll('.js-lead-form').forEach(form => {
            const place = form.dataset.place || 'unknown';

            // подставляем метки трафика скрытыми полями
            const hidden = {
                utm_source: traffic.utm_source, utm_medium: traffic.utm_medium,
                utm_campaign: traffic.utm_campaign, utm_content: traffic.utm_content,
                utm_term: traffic.utm_term, yclid: traffic.yclid,
                page_referrer: traffic.referrer || document.referrer,
                landing_page: traffic.first_landing || location.href,
                ym_client_id: ''
            };
            Object.entries(hidden).forEach(([k, v]) => {
                const i = document.createElement('input');
                i.type = 'hidden'; i.name = k; i.value = v || '';
                form.appendChild(i);
            });

            // цель «начал заполнять»
            let started = false;
            const fire = () => { if (!started) { started = true; goal('form_start', { place: place }); } };
            form.addEventListener('input', fire, true);
            form.addEventListener('change', fire, true);

            // маска телефона
            const phone = form.querySelector('input[name="phone"]');
            if (phone) {
                phone.setAttribute('inputmode', 'tel');
                phone.placeholder = '+7 (___) ___-__-__';
                const fmt = v => {
                    let d = v.replace(/\D/g, '');
                    if (d.startsWith('8')) d = '7' + d.slice(1);
                    if (!d.startsWith('7')) d = '7' + d;
                    d = d.slice(0, 11);
                    let o = '+7';
                    if (d.length > 1) o += ' (' + d.slice(1, 4);
                    if (d.length >= 4) o += ')';
                    if (d.length > 4) o += ' ' + d.slice(4, 7);
                    if (d.length > 7) o += '-' + d.slice(7, 9);
                    if (d.length > 9) o += '-' + d.slice(9, 11);
                    return o;
                };
                phone.addEventListener('input', () => { phone.value = fmt(phone.value); });
                phone.addEventListener('focus', () => { if (!phone.value) phone.value = '+7 ('; });
            }

            form.addEventListener('submit', async e => {
                e.preventDefault();
                const btn = form.querySelector('.js-submit');
                const status = form.querySelector('.js-status');
                const fd = new FormData(form);
                const digits = (fd.get('phone') || '').replace(/\D/g, '');
                status.hidden = true; status.className = 'form-status js-status';

                if (digits.length !== 11) {
                    status.className = 'form-status js-status error';
                    status.textContent = 'Проверьте номер телефона — нужно 11 цифр.';
                    status.hidden = false;
                    goal('form_error', { reason: 'phone', place: place });
                    return;
                }

                let cid = '';
                try { cid = await new Promise(res => {
                    if (!window.ym || !window.YM_ID) return res('');
                    let done = false;
                    ym(window.YM_ID, 'getClientID', id => { done = true; res(id || ''); });
                    setTimeout(() => { if (!done) res(''); }, 600);
                }); } catch (err) {}

                const data = {
                    name: (fd.get('name') || '').trim(),
                    phone: '+' + digits,
                    direction: fd.get('direction') || '',
                    age: fd.get('age') || '',
                    website: fd.get('website') || '',
                    consent: fd.get('consent') ? 'yes' : 'no',
                    consent_at: new Date().toISOString(),
                    form_place: place,
                    utm_source: fd.get('utm_source') || '', utm_medium: fd.get('utm_medium') || '',
                    utm_campaign: fd.get('utm_campaign') || '', utm_content: fd.get('utm_content') || '',
                    utm_term: fd.get('utm_term') || '', yclid: fd.get('yclid') || '',
                    ym_client_id: cid,
                    page_referrer: fd.get('page_referrer') || '', landing_page: fd.get('landing_page') || ''
                };

                btn.disabled = true; const old = btn.textContent; btn.textContent = 'Отправляем...';
                try {
                    const r = await fetch(FORM_ENDPOINT, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
                    const j = await r.json().catch(() => ({}));
                    if (r.ok && j.ok) {
                        status.className = 'form-status js-status success';
                        status.textContent = '\u2713 Заявка принята! Перезвоним в течение 10 минут.';
                        status.hidden = false;
                        goal('lead', { age: data.age, place: place, source: data.utm_source || 'direct/organic' });
                        form.reset();
                    } else {
                        let msg = 'Что-то пошло не так. Позвоните нам: +7 (912) 191-06-50';
                        if (j.error === 'too_fast') msg = 'Подождите 30 секунд перед повторной отправкой.';
                        if (j.error === 'invalid_fields') msg = 'Проверьте имя и телефон — что-то введено некорректно.';
                        status.className = 'form-status js-status error';
                        status.innerHTML = msg + '<div class="form-fallback">Или напишите в <a href="https://vk.me/your_scene_11sykt" target="_blank" rel="noopener">VK</a> — ответим так же быстро.</div>';
                        status.hidden = false;
                        goal('form_error', { reason: j.error || 'server', place: place });
                    }
                } catch (err) {
                    status.className = 'form-status js-status error';
                    status.innerHTML = 'Нет связи с сервером. Позвоните: <a href="tel:+79121910650">+7 (912) 191-06-50</a><div class="form-fallback">Или напишите в <a href="https://vk.me/your_scene_11sykt" target="_blank" rel="noopener">VK</a>.</div>';
                    status.hidden = false;
                    goal('form_error', { reason: 'network', place: place });
                } finally { btn.disabled = false; btn.textContent = old; }
            });
        });

        // ===== FAQ-АККОРДЕОН =====
        document.querySelectorAll('.faq-q').forEach(btn => {
            btn.addEventListener('click', () => {
                const item = btn.parentElement;
                const ans = item.querySelector('.faq-a');
                const open = item.classList.toggle('open');
                ans.style.maxHeight = open ? ans.scrollHeight + 'px' : '0';
                if (open) goal('faq_open');
            });
        });

        // ===== ВИДЕО =====
        (function () {
            const videos = document.querySelectorAll('#videoTrack video');
            if (!videos.length) return;
            const totalEl = document.getElementById('videoTotal'),
                  curEl = document.getElementById('videoCurrent'),
                  labelEl = document.getElementById('videoLabel');
            let i = 0;
            totalEl.textContent = videos.length;
            videos.forEach((v, n) => v.addEventListener('play', () => goal('video_play', { index: n + 1 }), { once: true }));
            function show(n) {
                videos.forEach(v => { v.classList.remove('active'); try { v.pause(); } catch (e) {} });
                videos[n].classList.add('active');
                videos[n].preload = 'metadata';
                curEl.textContent = n + 1;
                labelEl.textContent = 'Выступление #' + (n + 1) + ' — ученик «Твоя Сцена»';
            }
            document.getElementById('videoNext').addEventListener('click', () => { i = (i + 1) % videos.length; show(i); });
            document.getElementById('videoPrev').addEventListener('click', () => { i = (i - 1 + videos.length) % videos.length; show(i); });
        })();

        // ===== ЦЕЛЬ: ГЛУБОКИЙ ПРОСМОТР =====
        (function () {
            let fired = false;
            window.addEventListener('scroll', () => {
                if (fired) return;
                if ((window.scrollY + window.innerHeight) / document.body.scrollHeight > 0.6) { fired = true; goal('scroll_60'); }
            }, { passive: true });
        })();

        // ===== ПОЯВЛЕНИЕ БЛОКОВ =====
        (function () {
            const obs = new IntersectionObserver(es => es.forEach(en => {
                if (en.isIntersecting) { en.target.style.opacity = '1'; en.target.style.transform = 'translateY(0)'; }
            }), { threshold: 0.1 });
            document.querySelectorAll('.tl-item, .trial-item, .objection-card, .for-who-card, .advantage-item, .price-card').forEach(el => {
                el.style.opacity = '0'; el.style.transform = 'translateY(30px)'; el.style.transition = 'all 0.6s ease';
                obs.observe(el);
            });
        })();

        // ===== ЛЕТАЮЩИЕ НОТЫ =====
        (function () {
            const c = document.getElementById('notesCanvas');
            if (!c) return;
            const ctx = c.getContext('2d');
            const GLYPHS = ['\\u266a', '\\u266b', '\\u266c', '\\u2669'];
            let notes = [], raf;
            function resize() { c.width = innerWidth; c.height = innerHeight; }
            function init() {
                resize();
                const n = innerWidth < 768 ? 12 : 26;
                notes = Array.from({ length: n }, () => ({
                    x: Math.random() * c.width, y: Math.random() * c.height,
                    s: 12 + Math.random() * 20, v: 0.2 + Math.random() * 0.5,
                    g: GLYPHS[(Math.random() * GLYPHS.length) | 0], a: 0.15 + Math.random() * 0.35
                }));
            }
            function draw() {
                ctx.clearRect(0, 0, c.width, c.height);
                notes.forEach(p => {
                    ctx.globalAlpha = p.a;
                    ctx.fillStyle = '#FFD600';
                    ctx.font = p.s + 'px serif';
                    ctx.fillText(p.g, p.x, p.y);
                    p.y -= p.v;
                    if (p.y < -30) { p.y = c.height + 30; p.x = Math.random() * c.width; }
                });
                ctx.globalAlpha = 1;
                raf = requestAnimationFrame(draw);
            }
            addEventListener('resize', init);
            init(); draw();
        })();
"""


def esc(t):
    return html.escape(t, quote=False)


def build():
    cfg = json.load(io.open(os.path.join(BUILD, 'directions.json'), encoding='utf-8'))
    tpl = read(os.path.join(BUILD, 'template.html'))
    dirs = cfg['directions']
    show_prices = cfg.get('show_prices', False)
    prices = cfg.get('prices', [])
    built = []

    for d in dirs:
        url = '%s/%s/' % (SITE, d['slug'])

        trial = ''.join(
            '<div class="trial-item"><span class="trial-num">%02d</span><span class="trial-text">%s</span></div>'
            % (n + 1, esc(t)) for n, t in enumerate(d['trial']))

        timeline = ''.join(
            '<div class="tl-item"><div class="tl-when">%s</div><div class="tl-what">%s</div></div>'
            % (esc(t['when']), esc(t['what'])) for t in d['timeline'])

        objections = ''.join(
            '<div class="objection-card"><div class="objection-q">%s</div><div class="objection-a">%s</div></div>'
            % (esc(o['q']), esc(o['a'])) for o in d['objections'])

        for_who = ''.join(
            '<div class="for-who-card"><h3>%s</h3><p>%s</p></div>' % (esc(f['t']), esc(f['d']))
            for f in d['for_who'])

        faq = ''.join(
            '<div class="faq-item"><button class="faq-q" type="button">%s</button>'
            '<div class="faq-a"><p>%s</p></div></div>' % (esc(q['q']), esc(q['a']))
            for q in d['faq'])

        vids = d.get('videos') or ALL_VIDEOS
        videos = ''.join(
            '<video%s src="/videos/web/%s.mp4" poster="/assets/posters/%s.webp" controls preload="%s" playsinline></video>'
            % (' class="active"' if n == 0 else '', v, v, 'metadata' if n == 0 else 'none')
            for n, v in enumerate(vids))

        gal = d.get('gallery') or []
        if gal:
            cards = ''.join(
                '<img src="/assets/photos/%s" width="760" height="950" loading="lazy" decoding="async" alt="%s">'
                % (g['src'], esc(g['alt'])) for g in gal)
            gallery = ('<section class="gallery"><div class="section-title">'
                       '<h2>Наши ученики <span>на сцене</span></h2>'
                       '<p>Реальные фотографии с занятий и отчётных концертов. Без стоков.</p></div>'
                       '<div class="gallery-grid">%s</div></section>' % cards)
        else:
            gallery = ''

        others = [x for x in dirs if x['slug'] != d['slug']]
        other = ''.join(
            '<a class="other-dir" href="/%s/"><span class="od-icon">%s</span>%s</a>'
            % (x['slug'], x['icon'], esc(x['name'])) for x in others)
        footer_dirs = ''.join('<a href="/%s/">%s</a>' % (x['slug'], esc(x['name'])) for x in dirs)

        if show_prices and prices:
            cards = ''.join(
                '<div class="price-card%s"><div class="price-name">%s</div>'
                '<div class="price-value">%s</div><div class="price-note">%s</div></div>'
                % (' featured' if p.get('featured') else '', esc(p['name']), esc(p['value']), esc(p.get('note', '')))
                for p in prices)
            prices_block = ('<section class="prices" id="prices"><div class="section-title">'
                            '<h2>Сколько это <span>стоит</span></h2><p>Занятие 60 минут, индивидуально.</p></div>'
                            '<div class="prices-grid">%s</div></section>' % cards)
        else:
            prices_block = '<!-- Блок тарифов выключен. Включить: show_prices=true и заполнить prices в build/directions.json -->'

        schema = json.dumps({
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": ["MusicSchool", "LocalBusiness"],
                    "name": "Твоя Сцена — %s" % d['name'],
                    "description": d['description'],
                    "url": url,
                    "logo": SITE + "/assets/logo.png",
                    "image": SITE + "/assets/logo.png",
                    "telephone": "+7-912-191-06-50",
                    "address": {
                        "@type": "PostalAddress",
                        "streetAddress": "ул. Карла Маркса, 192",
                        "addressLocality": "Сыктывкар",
                        "addressRegion": "Республика Коми",
                        "addressCountry": "RU"
                    },
                    "areaServed": "Сыктывкар",
                    "sameAs": ["https://vk.com/your_scene_11sykt"]
                },
                {
                    "@type": "FAQPage",
                    "mainEntity": [
                        {"@type": "Question", "name": q['q'],
                         "acceptedAnswer": {"@type": "Answer", "text": q['a']}}
                        for q in d['faq']
                    ]
                }
            ]
        }, ensure_ascii=False, indent=None)

        page = tpl
        for k, v in {
            'TITLE': esc(d['title']), 'DESCRIPTION': esc(d['description']),
            'KEYWORDS': esc(d['keywords']), 'URL': url, 'YM_ID': str(YM_ID),
            'FORM_VALUE': d['form_value'], 'SCHEMA': schema,
            'CSS': BASE_CSS, 'EXTRA_CSS': EXTRA_CSS, 'JS': JS,
            'ICON': d['icon'], 'NAME': esc(d['name']), 'NAME_LOWER': esc(d['name_lower']),
            'H1': d['h1'], 'SUB': d['sub'],
            'TRIAL': trial, 'TIMELINE': timeline, 'OBJECTIONS': objections,
            'FOR_WHO': for_who, 'FAQ': faq, 'VIDEOS': videos,
            'OTHER': other, 'FOOTER_DIRS': footer_dirs, 'PRICES': prices_block,
            'HERO_IMG': d.get('hero_img', 'interior-1.webp'), 'GALLERY': gallery,
        }.items():
            page = page.replace('{{%s}}' % k, v)

        left = re.findall(r'\{\{[A-Z_]+\}\}', page)
        if left:
            raise SystemExit('Незаполненные плейсхолдеры в %s: %s' % (d['slug'], set(left)))

        out = os.path.join(ROOT, d['slug'], 'index.html')
        write(out, page)
        built.append((d['slug'], len(page)))
        print('  /%s/ — %.1f КБ' % (d['slug'], len(page) / 1024))

    # ---------- sitemap ----------
    today = datetime.date.today().isoformat()
    urls = ['<url><loc>%s/</loc><lastmod>%s</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>' % (SITE, today)]
    for d in dirs:
        urls.append('<url><loc>%s/%s/</loc><lastmod>%s</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>' % (SITE, quote(d['slug']), today))
    write(os.path.join(ROOT, 'sitemap.xml'),
          '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  '
          + '\n  '.join(urls) + '\n</urlset>\n')

    # GitHub Pages: без этого файла Jekyll может не отдать папки с кириллицей
    write(os.path.join(ROOT, '.nojekyll'), '')

    print('\nГотово: %d страниц, sitemap.xml обновлён.' % len(built))


if __name__ == '__main__':
    build()
