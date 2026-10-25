/* 思文败类 · 站点脚本（无依赖）
   所有 localStorage 读写都包在 try/catch 里：读者禁用存储时网站照常可用。 */
(function () {
  var doc = document.documentElement;
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* 深色模式 */
  $$('[data-theme-toggle]').forEach(function (b) {
    b.addEventListener('click', function () {
      var next = doc.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      doc.setAttribute('data-theme', next);
      store.set('theme', next);
    });
  });

  /* 手机菜单 */
  var mb = $('[data-menu-toggle]'), nav = $('#site-nav');
  if (mb && nav) {
    mb.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      mb.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  /* 字号 */
  $$('[data-fs]').forEach(function (b) {
    b.addEventListener('click', function () {
      var cur = parseInt(getComputedStyle(doc).getPropertyValue('--fs'), 10) || 18;
      var n = Math.max(14, Math.min(26, cur + parseInt(b.getAttribute('data-fs'), 10) * 2));
      doc.style.setProperty('--fs', n + 'px');
      store.set('fs', String(n));
    });
  });

  /* 回到顶部 */
  var top = $('[data-to-top]');
  if (top) {
    top.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
  }

  /* 阅读进度条 + 断点续读 */
  var bar = $('[data-progress] i');
  var reader = $('.reader[data-book]');
  var saveTimer = null;
  function onScroll() {
    var h = doc.scrollHeight - window.innerHeight;
    var p = h > 0 ? Math.min(1, window.scrollY / h) : 0;
    if (bar) bar.style.width = (p * 100).toFixed(1) + '%';
    if (top) top.classList.toggle('on', window.scrollY > 600);
    if (reader) {
      clearTimeout(saveTimer);
      saveTimer = setTimeout(function () {
        store.set('read:' + reader.getAttribute('data-book'), JSON.stringify({
          url: location.pathname, title: reader.getAttribute('data-chapter-title'), p: p
        }));
      }, 400);
    }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (reader) {
    try {
      var saved = JSON.parse(store.get('read:' + reader.getAttribute('data-book')) || 'null');
      if (saved && saved.url === location.pathname && saved.p > 0.03 && saved.p < 0.97 && !location.hash) {
        var h = doc.scrollHeight - window.innerHeight;
        window.scrollTo(0, h * saved.p);
      }
    } catch (e) {}
  }
  $$('[data-resume]').forEach(function (a) {
    try {
      var s = JSON.parse(store.get('read:' + a.getAttribute('data-resume')) || 'null');
      if (s && s.url) {
        a.href = s.url;
        a.textContent = '继续阅读：' + (s.title || '上次位置');
        a.hidden = false;
      }
    } catch (e) {}
  });

  /* 书架筛选 */
  var fb = $('.filterbar');
  if (fb) {
    fb.addEventListener('click', function (e) {
      var b = e.target.closest('[data-filter]');
      if (!b) return;
      $$('.chipbtn', fb).forEach(function (x) { x.classList.toggle('is-on', x === b); });
      var f = b.getAttribute('data-filter');
      $$('.book-card').forEach(function (c) {
        c.hidden = !(f === '*' || c.getAttribute('data-genre') === f);
      });
    });
  }

  /* 相册灯箱 */
  var links = $$('[data-lightbox]');
  if (links.length) {
    var lb = document.createElement('div');
    lb.className = 'lb'; lb.hidden = true; lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-label', '图片查看');
    lb.innerHTML = '<button class="x" aria-label="关闭">×</button><button class="pv" aria-label="上一张">‹</button><button class="nx" aria-label="下一张">›</button><img alt=""><p></p>';
    document.body.appendChild(lb);
    var im = $('img', lb), cap = $('p', lb), idx = 0;
    function show(i) {
      idx = (i + links.length) % links.length;
      im.src = links[idx].href;
      im.alt = links[idx].getAttribute('data-caption') || '';
      cap.textContent = im.alt;
      lb.hidden = false;
      document.body.style.overflow = 'hidden';
    }
    function hide() { lb.hidden = true; im.removeAttribute('src'); document.body.style.overflow = ''; }
    links.forEach(function (a, i) { a.addEventListener('click', function (e) { e.preventDefault(); show(i); }); });
    $('.x', lb).addEventListener('click', hide);
    $('.pv', lb).addEventListener('click', function () { show(idx - 1); });
    $('.nx', lb).addEventListener('click', function () { show(idx + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) hide(); });
    document.addEventListener('keydown', function (e) {
      if (lb.hidden) return;
      if (e.key === 'Escape') hide();
      if (e.key === 'ArrowLeft') show(idx - 1);
      if (e.key === 'ArrowRight') show(idx + 1);
    });
  }
})();
