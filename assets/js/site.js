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

})();
