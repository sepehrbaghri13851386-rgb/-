/* ============================================================
   بلو بانک — کارت به کارت (Blue Bank card to card)
   - کپی شماره کارت
   - مودال انتخاب روش پرداخت (checkout)
   - باز/بسته کردن گزینهٔ کارت به کارت در مرحلهٔ ۲
   ============================================================ */
(function () {
    'use strict';

    /* ---------------- helpers ---------------- */

    function legacyCopy(text) {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');
        ta.style.position = 'fixed';
        ta.style.top = '-1000px';
        document.body.appendChild(ta);
        ta.select();
        var done = false;
        try {
            done = document.execCommand('copy');
        } catch (err) {
            done = false;
        }
        document.body.removeChild(ta);
        return done;
    }

    function copyText(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text).catch(function () {
                // اگر مرورگر اجازه نداد، روش قدیمی متن را کپی می‌کند
                return legacyCopy(text) ? undefined : Promise.reject(new Error('copy failed'));
            });
        }
        return legacyCopy(text)
            ? Promise.resolve()
            : Promise.reject(new Error('copy failed'));
    }

    /* ---------------- copy the card number ---------------- */

    document.addEventListener('click', function (e) {
        var btn = e.target.closest ? e.target.closest('[data-bb-copy]') : null;
        if (!btn) return;
        e.preventDefault();

        var tools = btn.closest('.bb-tools');
        var msg = tools ? tools.querySelector('.bb-copy-msg') : null;
        var original = btn.getAttribute('data-label') || btn.textContent.trim();
        btn.setAttribute('data-label', original);

        copyText(btn.getAttribute('data-bb-copy')).then(function () {
            btn.classList.add('is-done');
            btn.textContent = 'کپی شد ✓';
            if (msg) msg.textContent = 'شماره کارت در حافظهٔ دستگاه کپی شد.';
            setTimeout(function () {
                btn.classList.remove('is-done');
                btn.textContent = original;
                if (msg) msg.textContent = '';
            }, 2600);
        }).catch(function () {
            if (msg) msg.textContent = 'کپی خودکار ممکن نشد؛ شمارهٔ کارت را دستی بردارید.';
        });
    });

    /* ---------------- payment-method modal ---------------- */

    var modal = document.getElementById('pmModal');

    function openModal() {
        if (!modal) return;
        var first = modal.querySelector('.pm-opt[data-pm-panel]');
        if (first) first.click();
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('no-scroll');
    }

    function closeModal() {
        if (!modal) return;
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('no-scroll');
    }

    if (modal) {
        Array.prototype.forEach.call(document.querySelectorAll('[data-pm-open]'), function (trigger) {
            trigger.addEventListener('click', function (e) {
                e.preventDefault();
                openModal();
            });
        });

        Array.prototype.forEach.call(modal.querySelectorAll('[data-pm-close]'), function (btn) {
            btn.addEventListener('click', closeModal);
        });

        modal.addEventListener('click', function (e) {
            if (e.target === modal) closeModal();
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' || e.keyCode === 27) closeModal();
        });

        Array.prototype.forEach.call(modal.querySelectorAll('.pm-opt[data-pm-panel]'), function (opt) {
            opt.addEventListener('click', function () {
                var panel = modal.querySelector('#' + opt.getAttribute('data-pm-panel'));
                if (!panel) return;
                Array.prototype.forEach.call(modal.querySelectorAll('.pm-opt'), function (o) {
                    o.classList.remove('is-active');
                    o.setAttribute('aria-selected', 'false');
                });
                Array.prototype.forEach.call(modal.querySelectorAll('.pm-panel'), function (p) {
                    p.classList.remove('is-active');
                });
                opt.classList.add('is-active');
                opt.setAttribute('aria-selected', 'true');
                panel.classList.add('is-active');

                // دکمهٔ پایین مودال با روش انتخاب‌شده هماهنگ می‌شود
                var cta = modal.querySelector('#pmCta');
                var label = cta ? cta.querySelector('.pm-cta-label') : null;
                var href = opt.getAttribute('data-pm-href');
                if (cta && href) cta.setAttribute('href', href);
                if (label && opt.getAttribute('data-pm-label')) {
                    label.textContent = opt.getAttribute('data-pm-label');
                }

                // روش انتخاب‌شده در فیلد مخفی فرم اطلاعات ثبت می‌شود
                var payField = document.getElementById('pmPayment');
                if (payField && opt.getAttribute('data-pm-value')) {
                    payField.value = opt.getAttribute('data-pm-value');
                }
            });
        });

        // دکمهٔ پایان مودال: فرم اطلاعات ارسال را (با روش پرداخت انتخابی) ثبت می‌کند
        var pmCta = modal.querySelector('#pmCta');
        if (pmCta) {
            pmCta.addEventListener('click', function (e) {
                e.preventDefault();
                closeModal();
                var form = document.getElementById('checkoutInfoForm');
                if (form) {
                    if (typeof form.requestSubmit === 'function') form.requestSubmit();
                    else form.submit();
                }
            });
        }
    }

    /* ---------------- step 2: toggle the option block ---------------- */

    Array.prototype.forEach.call(document.querySelectorAll('[data-bb-toggle]'), function (head) {
        head.addEventListener('click', function (e) {
            e.preventDefault();
            var box = head.closest('.bb-opt');
            if (box) box.classList.toggle('is-open');
        });
    });
})();
