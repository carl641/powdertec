/* PowderTec — site behaviour
   -------------------------------------------------------------------------
   Set FORM_ENDPOINT to a POST URL (Formspree, Netlify Forms, your own handler)
   to have the contact form submit server-side. While it is empty the form
   validates in the browser and then hands off to the visitor's mail client so
   nothing is lost.
   ------------------------------------------------------------------------- */
(function () {
  'use strict';

  var FORM_ENDPOINT = '';
  var FORM_TO = 'info@alabamapowdercoating.com';

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

  /* ---- contact form ---- */
  var form = document.getElementById('quote-form');
  if (!form) return;

  var status = form.querySelector('.form__status');

  var say = function (msg) {
    if (!status) return;
    status.textContent = msg;
    status.classList.add('is-on');
    status.setAttribute('role', 'status');
  };

  var markField = function (input, bad, msg) {
    var field = input.closest('.field');
    if (!field) return;
    field.classList.toggle('is-bad', bad);
    input.setAttribute('aria-invalid', bad ? 'true' : 'false');
    var err = field.querySelector('.err');
    if (err && msg) err.textContent = msg;
  };

  var validate = function (input) {
    var val = (input.value || '').trim();
    var required = input.hasAttribute('required');

    if (required && !val) {
      markField(input, true, input.dataset.msgRequired || 'This field is required.');
      return false;
    }
    if (input.type === 'email' && val && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(val)) {
      markField(input, true, 'Enter a valid email address.');
      return false;
    }
    if (input.type === 'tel' && val && val.replace(/\D/g, '').length < 10) {
      markField(input, true, 'Enter a 10-digit phone number.');
      return false;
    }
    markField(input, false);
    return true;
  };

  var inputs = form.querySelectorAll('input, select, textarea');
  Array.prototype.forEach.call(inputs, function (input) {
    input.addEventListener('blur', function () { validate(input); });
    input.addEventListener('input', function () {
      if (input.closest('.field') && input.closest('.field').classList.contains('is-bad')) validate(input);
    });
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    var firstBad = null;
    Array.prototype.forEach.call(inputs, function (input) {
      if (!validate(input) && !firstBad) firstBad = input;
    });

    if (firstBad) {
      say('Please correct the highlighted fields and try again.');
      firstBad.focus();
      return;
    }

    var data = new FormData(form);

    if (FORM_ENDPOINT) {
      var btn = form.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }
      fetch(FORM_ENDPOINT, { method: 'POST', body: data, headers: { Accept: 'application/json' } })
        .then(function (r) {
          if (!r.ok) throw new Error('bad response');
          form.reset();
          say('Thank you — your request is in. We will get back to you shortly. Need an answer today? Call (256) 287-3031.');
        })
        .catch(function () {
          say('Something went wrong sending the form. Please call (256) 287-3031 or email ' + FORM_TO + '.');
        })
        .then(function () {
          if (btn) { btn.disabled = false; btn.textContent = 'Send Message'; }
        });
      return;
    }

    // No endpoint configured — hand off to the visitor's mail client.
    var lines = [
      'Name: '         + (data.get('name')    || ''),
      'Company: '      + (data.get('company') || '—'),
      'Email: '        + (data.get('email')   || ''),
      'Phone: '        + (data.get('phone')   || '—'),
      'Project type: ' + (data.get('project') || ''),
      '',
      'Project details:',
      (data.get('message') || '')
    ];
    var href = 'mailto:' + FORM_TO +
      '?subject=' + encodeURIComponent('Quote request — ' + (data.get('project') || 'Project') + ' — ' + (data.get('name') || '')) +
      '&body=' + encodeURIComponent(lines.join('\n'));

    say('Opening your email app with the request ready to send. If nothing happens, email ' + FORM_TO + ' or call (256) 287-3031.');
    window.location.href = href;
  });
})();
