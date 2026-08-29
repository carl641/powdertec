/* PowderTec — site behaviour
   -------------------------------------------------------------------------
   The contact page uses a hosted Jotform embed, so no form handling lives
   here.
   ------------------------------------------------------------------------- */
(function () {
  'use strict';

  /* ---- sticky header state ---- */
  var hdr = document.getElementById('hdr');
  if (hdr) {
    var onScroll = function () {
      hdr.classList.toggle('is-stuck', window.scrollY > 12);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---- mobile navigation ---- */
  var burger = document.querySelector('.burger');
  var nav = document.getElementById('nav');
  if (burger && nav) {
    var setNav = function (open) {
      burger.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('is-open', open);
      document.body.classList.toggle('nav-open', open);
    };
    burger.addEventListener('click', function () {
      setNav(burger.getAttribute('aria-expanded') !== 'true');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) setNav(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setNav(false);
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 1024) setNav(false);
    });
  }

  /* ---- scroll reveal ---- */
  var reveals = document.querySelectorAll('[data-reveal]');
  if (reveals.length) {
    if (!('IntersectionObserver' in window)) {
      Array.prototype.forEach.call(reveals, function (el) { el.classList.add('is-in'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-in');
          io.unobserve(entry.target);
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

      Array.prototype.forEach.call(reveals, function (el) {
        // stagger siblings that share a parent group
        var group = el.parentElement;
        if (group && group.hasAttribute('data-stagger')) {
          var i = Array.prototype.indexOf.call(group.children, el);
          el.style.setProperty('--d', (i * 90) + 'ms');
        }
        io.observe(el);
      });
    }
  }

  /* ---- footer year ---- */
  var yr = document.querySelectorAll('[data-year]');
  Array.prototype.forEach.call(yr, function (el) { el.textContent = new Date().getFullYear(); });


  /* ---- powder-gun cursor ----------------------------------------------
     Replaces the pointer with a spray gun; holding the primary button lays
     down coating that burns off after ten seconds. Desktop only, and never
     when the visitor has asked for reduced motion. */
  (function powderGun() {
    var gun   = document.getElementById('pg-gun');
    var coat  = document.getElementById('pg-coat');
    var spray = document.getElementById('pg-spray');
    if (!gun || !coat || !spray) return;

    if (!window.matchMedia) return;
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    /* Fields want a real caret, and a cross-origin frame swallows the pointer
       outright — no hover, no moves reach us, so the gun would stall on its
       edge. Both hand the native cursor back: fields by hit-testing the event,
       frames by the halo around their box, since we only ever see the last
       move before the pointer crosses in. */
    var FIELDS = 'input, textarea, select, [contenteditable=""], [contenteditable="true"]';
    var FRAMES = 'iframe, embed, object, [data-no-gun]';
    var HALO   = 30;          // px of clearance around a frame

    var MAX_DUST    = 300;    // live nodes per layer — keeps long holds cheap
    var MAX_SPLOTCH = 90;
    var DUST_MS     = 600;
    var COAT_MS     = 10000;

    var root = document.documentElement;
    var x = 0, y = 0, placed = false, queued = false;
    var onField = false, firing = false, dustTimer = null, coatTimer = null;
    var zones = [], remeasure = true;

    /* ---- the off switch ---------------------------------------------------
       .pg-ready reveals the button, so it only shows where the gun can
       actually run. The choice is remembered per visitor and read back on
       every page, which matters on a four-page site — turning it off once
       has to stick. */
    var STORE  = 'pg-cursor';
    var toggle = document.getElementById('pg-toggle');
    var state  = document.getElementById('pg-toggle-state');
    var live   = true;

    function remember(value) {
      try { localStorage.setItem(STORE, value); } catch (err) { /* private mode */ }
    }

    function recall() {
      try { return localStorage.getItem(STORE); } catch (err) { return null; }
    }

    function empty(layer) {
      while (layer.firstChild) layer.removeChild(layer.firstChild);
    }

    function setLive(next, persist) {
      live = next;
      root.classList.toggle('pg-on', live && placed);
      if (!live) {
        stop();
        root.classList.remove('pg-rest');
        empty(spray);
        empty(coat);          // wipe the coating already on the page
      }
      if (toggle) {
        toggle.setAttribute('aria-pressed', String(live));
        toggle.title = 'Turn the spray-gun cursor ' + (live ? 'off' : 'on');
        if (state) state.textContent = live ? 'On' : 'Off';
      }
      if (persist) remember(live ? 'on' : 'off');
    }

    root.classList.add('pg-ready');
    if (toggle) {
      toggle.addEventListener('click', function () { setLive(!live, true); });
    }
    setLive(recall() !== 'off', false);

    /* ---- where the gun is not welcome ---- */
    function measure() {
      remeasure = false;
      zones = [];
      Array.prototype.forEach.call(document.querySelectorAll(FRAMES), function (el) {
        var r = el.getBoundingClientRect();
        if (r.width && r.height) {
          zones.push([r.left - HALO, r.top - HALO, r.right + HALO, r.bottom + HALO]);
        }
      });
    }

    function inZone(px, py) {
      if (remeasure) measure();
      for (var i = 0; i < zones.length; i++) {
        var z = zones[i];
        if (px >= z[0] && px <= z[2] && py >= z[1] && py <= z[3]) return true;
      }
      return false;
    }

    function settle() {
      var off = onField || inZone(x, y);
      root.classList.toggle('pg-rest', off);
      if (off) stop();
      return off;
    }

    /* ---- follow the pointer ---- */
    function draw() {
      queued = false;
      gun.style.transform = 'translate3d(' + x + 'px, ' + (y - 29) + 'px, 0)';
    }

    function move(e) {
      x = e.clientX;                    // tracked even when off, so switching
      y = e.clientY;                    // back on puts the gun under the hand
      if (!live) return;
      if (!placed) { placed = true; root.classList.add('pg-on'); }
      settle();
      // keep drawing even while hidden, so it never reappears a frame behind
      if (!queued) { queued = true; requestAnimationFrame(draw); }
    }

    function field(e) {
      if (!live) return;
      onField = !!(e.target && e.target.closest && e.target.closest(FIELDS));
      settle();
    }

    /* ---- the spray itself ---- */
    function nozzle() {
      var box = gun.getBoundingClientRect();
      return { x: box.left, y: box.top + box.height * (50.5 / 120) };
    }

    function puff() {
      if (spray.childElementCount > MAX_DUST) return;
      var tip = nozzle();

      for (var i = 0; i < 9; i++) {
        var bit = document.createElement('div');
        var size = 2 + Math.random() * 5;
        bit.className = 'pg-dust';
        bit.style.left = (tip.x - 3) + 'px';
        bit.style.top = (tip.y - 3 + (Math.random() - 0.5) * 5) + 'px';
        bit.style.width = size + 'px';
        bit.style.height = size + 'px';
        bit.style.setProperty('--mx', -(50 + Math.random() * 110) + 'px');
        bit.style.setProperty('--my', ((Math.random() - 0.5) * 60) + 'px');
        spray.appendChild(bit);
        setTimeout(sweep(bit), DUST_MS);
      }
    }

    function coating() {
      if (coat.childElementCount > MAX_SPLOTCH) return;
      var tip = nozzle();

      // the gun points left, so the coating lands ahead of the nozzle
      var hitX = tip.x - (75 + Math.random() * 65);
      var hitY = tip.y + (Math.random() - 0.5) * 48;

      var w = 14 + Math.random() * 24;
      var h = 10 + Math.random() * 20;

      var blob = document.createElement('div');
      blob.className = 'pg-splotch';
      blob.style.width = w + 'px';
      blob.style.height = h + 'px';
      blob.style.left = (hitX - w / 2) + 'px';
      blob.style.top = (hitY - h / 2) + 'px';
      blob.style.setProperty('--rot', (Math.random() * 360) + 'deg');
      coat.appendChild(blob);
      setTimeout(sweep(blob), COAT_MS);

      var flecks = 2 + Math.floor(Math.random() * 4);
      for (var i = 0; i < flecks; i++) {
        var fleck = document.createElement('div');
        var size = 2 + Math.random() * 5;
        fleck.className = 'pg-fleck';
        fleck.style.width = size + 'px';
        fleck.style.height = size + 'px';
        fleck.style.left = (hitX + (Math.random() - 0.5) * 35) + 'px';
        fleck.style.top = (hitY + (Math.random() - 0.5) * 35) + 'px';
        coat.appendChild(fleck);
        setTimeout(sweep(fleck), COAT_MS);
      }
    }

    function sweep(node) {
      return function () { if (node.parentNode) node.parentNode.removeChild(node); };
    }

    /* ---- trigger ---- */
    function start(e) {
      if (e.button !== 0 || firing || !placed || !live) return;
      if (root.classList.contains('pg-rest')) return;

      firing = true;
      root.classList.add('pg-firing');
      puff();
      coating();
      dustTimer = setInterval(puff, 28);
      coatTimer = setInterval(coating, 90);   // slower, so the DOM stays light
    }

    function stop() {
      if (!firing) return;
      firing = false;
      root.classList.remove('pg-firing');
      clearInterval(dustTimer);
      clearInterval(coatTimer);
      dustTimer = coatTimer = null;
    }

    /* frame rects move with the page, and embeds arrive late (Jotform) */
    var stale = function () { remeasure = true; };
    window.addEventListener('scroll', stale, { passive: true });
    window.addEventListener('resize', stale);
    window.addEventListener('load', stale);
    if (window.MutationObserver) {
      new MutationObserver(function (records) {
        // our own particles churn the two layers constantly — ignore those
        for (var i = 0; i < records.length; i++) {
          var box = records[i].target;
          if (box !== coat && box !== spray) { stale(); return; }
        }
      }).observe(document.body, { childList: true, subtree: true });
    }

    document.addEventListener('mousemove', move, { passive: true });
    document.addEventListener('mouseover', field, { passive: true });
    document.addEventListener('mousedown', start);
    document.addEventListener('mouseup', stop);
    document.addEventListener('mouseleave', stop);
    document.addEventListener('contextmenu', stop);
    document.addEventListener('visibilitychange', stop);
    window.addEventListener('blur', stop);
  })();

})();
