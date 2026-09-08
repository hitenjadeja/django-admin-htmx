/* Django admin transport and widget lifecycle for HTMX 4.0.0. */
(() => {
    'use strict';
    if (window.AdminHTMX) return;
    const nonce = document.currentScript?.nonce;
    if (nonce) window.htmx.config.inlineScriptNonce = nonce;
    const loaded = new Set();
    const pageListeners = [];
    let hydrating = false;
    let requests = 0;
    let loadingTimer;
    let loadingVisible = false;
    let navigated = false;
    let stylesReady = Promise.resolve();
    const labels = document.querySelector('meta[name="admin-htmx-labels"]')?.dataset || {};
    const root = document.querySelector('meta[name="admin-htmx-root"]')?.content;
    const emit = (name, detail = {}) => document.dispatchEvent(new CustomEvent(`admin-htmx:${name}`, {detail}));
    const stock = (url, name) => new URL(url || location.href, location.href).pathname.replace(/\.[a-f0-9]{12}\./g, '.').endsWith(`/admin/js/${name}`);
    const isPageScript = url => ['theme.js', 'nav_sidebar.js', 'filters.js', 'cancel.js', 'unusable_password_field.js', 'prepopulate_init.js', 'change_form.js'].some(name => stock(url, name));
    const owned = ctx => ctx?.request?.headers?.['X-Admin-HTMX'] === 'true' || ctx?.request?.headers?.['HX-History-Restore-Request'] === 'true';

    // Capture only global listeners registered during synchronous stock-widget
    // initialization. Restore native methods immediately; don't patch events globally.
    function scoped(fn) {
        const originals = [document.addEventListener, window.addEventListener];
        [document, window].forEach((target, i) => {
            target.addEventListener = function (type, callback, options) {
                pageListeners.push(() => target.removeEventListener(type, callback, options));
                return originals[i].call(target, type, callback, options);
            };
        });
        try { return fn(); }
        finally {
            document.addEventListener = originals[0];
            window.addEventListener = originals[1];
        }
    }

    function status() {
        let box = document.getElementById('admin-htmx-status');
        if (!box) {
            box = document.createElement('p');
            box.className = 'visually-hidden';
            box.id = 'admin-htmx-status';
            box.setAttribute('role', 'status');
            box.setAttribute('aria-live', 'polite');
            (document.getElementById('header') || document.getElementById('content') || document.body).append(box);
        }
        return box;
    }

    function stopLoading() {
        clearTimeout(loadingTimer);
        loadingTimer = undefined;
        loadingVisible = false;
    }

    function busy() {
        const active = hydrating || requests > 0;
        document.getElementById('content-start')?.setAttribute('aria-busy', String(active));
        const box = status();
        if (active && box.dataset.state !== 'error') {
            box.className = loadingVisible ? 'admin-htmx-loading' : 'visually-hidden';
            box.removeAttribute('tabindex');
            (document.getElementById('header') || document.getElementById('content') || document.body).append(box);
            const message = labels.loading || 'Loading…';
            if (box.textContent !== message) box.textContent = message;
            box.dataset.state = 'loading';
            // Keep one delay across redirects and body/widget initialization.
            if (!loadingVisible && loadingTimer === undefined) {
                loadingTimer = setTimeout(() => {
                    loadingTimer = undefined;
                    if (!(hydrating || requests > 0) || status().dataset.state === 'error') return;
                    loadingVisible = true;
                    status().className = 'admin-htmx-loading';
                }, 200);
            }
        } else if (!active) {
            stopLoading();
            if (box.dataset.state !== 'error') {
                box.className = 'visually-hidden';
                box.textContent = '';
                delete box.dataset.state;
            }
        }
    }

    function error(message) {
        stopLoading();
        status().textContent = message || labels.error || 'The request could not be completed. Your entries are still here. Please try again.';
        status().dataset.state = 'error';
        status().className = 'errornote';
        document.getElementById('content')?.prepend(status());
        status().setAttribute('tabindex', '-1');
        status().focus();
        emit('error', {message});
    }

    function cleanup() {
        emit('before-swap');
        while (pageListeners.length) pageListeners.pop()();
        window.dismissChildPopups?.();
        const dates = window.DateTimeShortcuts;
        if (dates) {
            [...dates.dismissClockFunc, ...dates.dismissCalendarFunc].forEach(fn => document.removeEventListener('click', fn));
            ['calendars', 'calendarInputs', 'clockInputs', 'dismissClockFunc', 'dismissCalendarFunc'].forEach(key => { dates[key] = []; });
        }
        const $ = window.django?.jQuery;
        if ($) {
            $('.admin-autocomplete.select2-hidden-accessible').each(function () { $(this).select2('destroy'); });
            $.cleanData([...document.body.querySelectorAll('*')]);
        }
        if (window.SelectBox) window.SelectBox.cache = {};
    }

    // Load stock definitions once and replay only scripts whose work belongs to a
    // single page. Keep script data placeholders for Django's constant lookups.
    async function script(node) {
        const src = node.dataset.adminHtmxSrc;
        const once = node.dataset.adminHtmxLoad === 'once';
        const key = src || node.textContent;
        if (loaded.has(key) && (once || (src && !isPageScript(src) && node.dataset.adminHtmxLoad !== 'page'))) return false;
        const element = document.createElement('script');
        if (nonce) element.nonce = nonce;
        for (const attr of node.attributes) {
            if (!['src', 'type', 'id', 'nonce'].includes(attr.name) && !attr.name.startsWith('data-admin-htmx')) element.setAttribute(attr.name, attr.value);
        }
        if (node.dataset.adminHtmxType) element.type = node.dataset.adminHtmxType;
        const $ = window.django?.jQuery;
        const ready = $?.fn.ready;
        const previousJQuery = window.jQuery;
        const select2Vendor = src && /\/admin\/js\/vendor\/select2\//.test(src);
        if ($ && select2Vendor) window.jQuery = $;
        const originalAdd = window.addEventListener;
        const loadCallbacks = [];
        const skipReady = ['inlines.js', 'autocomplete.js'].some(name => stock(src, name));
        if ($) $.fn.ready = function (fn) { if (!skipReady) fn.call(document, $); return this; };
        window.addEventListener = function (type, fn, opts) {
            if (type === 'load') loadCallbacks.push(fn);
            else originalAdd.call(window, type, fn, opts);
        };
        const originalDocumentAdd = document.addEventListener;
        if (stock(src, 'actions.js')) {
            document.addEventListener = function (type, fn, opts) {
                pageListeners.push(() => document.removeEventListener(type, fn, opts));
                originalDocumentAdd.call(document, type, fn, opts);
            };
            window.addEventListener = function (type, fn, opts) {
                pageListeners.push(() => window.removeEventListener(type, fn, opts));
                originalAdd.call(window, type, fn, opts);
            };
        }
        try {
            if (src) {
                element.src = src;
                element.async = false;
                await new Promise((resolve, reject) => {
                    element.onload = resolve;
                    element.onerror = () => reject(new Error(`Could not load ${src}`));
                    document.head.append(element);
                });
            } else if (element.type === 'module') {
                element.textContent = node.textContent;
                await new Promise((resolve, reject) => {
                    element.onload = resolve;
                    element.onerror = reject;
                    document.head.append(element);
                });
            } else {
                element.textContent = node.textContent;
                document.head.append(element);
            }
            loaded.add(key);
            if (!stock(src, 'admin/DateTimeShortcuts.js') && !stock(src, 'SelectFilter2.js')) {
                loadCallbacks.forEach(fn => fn.call(window, new Event('load')));
            }
        } finally {
            if ($) $.fn.ready = ready;
            if ($ && select2Vendor) window.jQuery = previousJQuery;
            window.addEventListener = originalAdd;
            document.addEventListener = originalDocumentAdd;
            element.remove();
        }
        return true;
    }

    function initializeWidgets(newActions) {
        const $ = window.django?.jQuery;
        if ($?.fn.stackedFormset) {
            $('.js-inline-admin-formset').each(function () {
                const data = $(this).data();
                const opts = data.inlineFormset;
                const stacked = data.inlineType === 'stacked';
                const selector = opts.name + (stacked ? '-group .inline-related' : '-group .tabular.inline-related tbody:first > tr.form-row');
                $(selector)[stacked ? 'stackedFormset' : 'tabularFormset'](selector, opts.options);
            });
        }
        if (window.DateTimeShortcuts) {
            const dates = window.DateTimeShortcuts;
            if (!dates.init.adminHtmx) {
                const original = dates.init;
                dates.init = () => scoped(original);
                dates.init.adminHtmx = true;
            }
            dates.init();
        }
        document.querySelectorAll('select.selectfilter, select.selectfilterstacked').forEach(el => {
            window.SelectFilter?.init(el.id, el.dataset.fieldName, Number(el.dataset.isStacked));
        });
        if ($?.fn.djangoAdminSelect2) $('.admin-autocomplete').not('[name*=__prefix__]').djangoAdminSelect2();
        if ($) $('.related-widget-wrapper select').trigger('change');
        if (!newActions && window.Actions && document.querySelector('tr input.action-select')) {
            scoped(() => window.Actions(document.querySelectorAll('tr input.action-select')));
        }
    }

    function inSite(href) {
        try {
            const url = new URL(href, location.href);
            return url.origin === location.origin && url.pathname.startsWith(root) && !url.searchParams.has('_popup');
        } catch { return false; }
    }

    function decorate() {
        document.body.setAttribute('hx-history-elt', '');
        const disabled = ' [data-admin-htmx="off"], [hx-boost="false"]';
        document.querySelectorAll('a[href], form').forEach(el => {
            if (el.closest(disabled) || el.hasAttribute('hx-get') || el.hasAttribute('hx-post')) return;
            const form = el.tagName === 'FORM';
            const href = form ? el.action : el.href;
            if (!inSite(href) || el.target && el.target !== '_self' || el.hasAttribute('download')) return;
            if (!form && (el.getAttribute('href').startsWith('#') || el.matches('.related-widget-wrapper-link, .related-lookup, [data-popup-opener], .add-row a, .inline-deletelink, .deletelink-box a[href="#"], .cancel-link'))) return;
            // Django uses javascript-free event-driven anchors for calendars and
            // inlines. Only real navigation URLs are enhanced.
            if (!form && el.closest('.datetimeshortcuts, .calendarbox, .clockbox, .selector, .actions')) return;
            el.setAttribute('hx-boost', 'true');
            el.setAttribute('hx-target', 'body');
            el.setAttribute('hx-select', 'body');
            el.setAttribute('hx-swap', 'outerSync');
            el.setAttribute('hx-sync', 'body:drop');
            el.setAttribute('hx-headers', '{"X-Admin-HTMX":"true"}');
            if (form && !el.hasAttribute('hx-disable')) el.setAttribute('hx-disable', 'findAll input[type=submit]:not(:disabled), findAll button[type=submit]:not(:disabled), findAll button:not([type]):not(:disabled)');
            if (!form || el.method.toLowerCase() === 'get') el.setAttribute('hx-push-url', 'true');
        });
        window.htmx.process(document.body);
    }

    async function hydrate() {
        hydrating = true;
        busy();
        try {
            await stylesReady;
            let newActions = false;
            const deferred = [];
            for (const node of document.querySelectorAll('[data-admin-htmx-script]')) {
                const src = node.dataset.adminHtmxSrc;
                if (isPageScript(src)) deferred.push(node);
                else if (await script(node)) newActions ||= stock(src, 'actions.js');
            }
            for (const node of deferred) await script(node);
            initializeWidgets(newActions);
            decorate();
            if (navigated) {
                const focus = document.querySelector('.errorlist') || document.querySelector('[autofocus]') || document.getElementById('content-start');
                if (focus) {
                    if (!focus.matches('input,select,textarea,button,a')) focus.setAttribute('tabindex', '-1');
                    focus.focus({preventScroll: true});
                }
                window.scrollTo(0, 0);
            }
            emit('load', {root: document.body});
        } catch (e) {
            console.error('AdminHTMX initialization failed', e);
            error('Some controls could not be initialized. Reload this page before continuing.');
        } finally {
            hydrating = false;
            busy();
        }
    }

    function updateHead(doc) {
        const selector = 'link[rel="stylesheet"], style';
        const existing = [...document.head.querySelectorAll(selector)];
        const pending = [];
        const signature = element => JSON.stringify([
            element.tagName,
            [...element.attributes].filter(attr => attr.name !== 'nonce')
                .map(attr => [attr.name, attr.value]).sort(),
            element.textContent,
        ]);
        // Match the incoming document's stylesheet set AND cascade order. Keeping
        // a previous form/list stylesheet would subtly restyle later pages.
        for (const incoming of doc.head.querySelectorAll(selector)) {
            const index = existing.findIndex(element => signature(element) === signature(incoming));
            let element;
            if (index >= 0) {
                [element] = existing.splice(index, 1);
            } else {
                element = incoming.cloneNode(true);
                if (nonce) element.nonce = nonce;
                if (element.tagName === 'LINK') {
                    pending.push(new Promise((resolve, reject) => {
                        element.onload = resolve;
                        element.onerror = () => reject(new Error(`Could not load ${element.href}`));
                    }));
                }
            }
            document.head.append(element);
        }
        existing.forEach(element => element.remove());
        stylesReady = Promise.all(pending);
        document.head.querySelectorAll('[data-admin-htmx-script]').forEach(element => element.remove());
        doc.head.querySelectorAll('[data-admin-htmx-script]').forEach(element => document.head.append(element.cloneNode(true)));
        ['lang', 'dir'].forEach(attr => document.documentElement.setAttribute(attr, doc.documentElement.getAttribute(attr) || ''));
    }

    window.AdminHTMX = {version: '0.1.1', hydrate, get busy() { return hydrating || requests > 0; }, get listenerCount() { return pageListeners.length; }};
    if (!root || document.body.classList.contains('popup') || !document.querySelector('meta[name="admin-htmx-enhanced"]')) return;
    document.addEventListener('htmx:config:request', event => {
        const ctx = event.detail.ctx;
        if (owned(ctx)) ctx.request.headers['X-Admin-HTMX'] = 'true';
    });
    document.addEventListener('htmx:before:request', event => {
        if (!owned(event.detail.ctx)) return;
        if (hydrating) { event.preventDefault(); return; }
        requests++;
        delete status().dataset.state;
        busy();
    });
    document.addEventListener('htmx:before:response', event => {
        const ctx = event.detail.ctx;
        if (!owned(ctx)) return;
        const response = ctx.response.raw;
        if (response.headers.get('Content-Disposition')?.includes('attachment')) {
            event.preventDefault();
            ctx.extensionPromise = (async () => {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = response.headers.get('Content-Disposition').match(/filename="?([^";]+)/)?.[1] || 'download';
                link.click();
                setTimeout(() => URL.revokeObjectURL(url), 60000);
                emit('download');
            })();
        } else if (response.status >= 400) {
            // Never replace an unsaved form with a generic error page or retry a POST.
            event.preventDefault();
            error(response.status === 403 ? 'This request was refused. Check your session and permissions, then reload the page.' : undefined);
        }
    });
    document.addEventListener('htmx:after:request', event => {
        const ctx = event.detail.ctx;
        if (!owned(ctx) || ctx.hx.location || ctx.hx.redirect || !ctx.text) return;
        const doc = new DOMParser().parseFromString(ctx.text, 'text/html');
        if (!doc.querySelector('meta[name="admin-htmx-enhanced"]')) {
            event.preventDefault();
            if (ctx.request.method === 'GET') location.assign(ctx.response.raw.url || ctx.request.action);
            else error('This response requires a full page. Reload before continuing.');
            return;
        }
        updateHead(doc);
    });
    document.addEventListener('htmx:before:swap', event => {
        if (owned(event.detail.ctx)) { cleanup(); hydrating = true; }
    });
    document.addEventListener('htmx:after:swap', event => {
        if (owned(event.detail.ctx)) { navigated = true; hydrate(); }
    });
    document.addEventListener('htmx:finally:request', event => {
        if (owned(event.detail.ctx)) { requests = Math.max(0, requests - 1); busy(); }
    });
    document.addEventListener('htmx:error', event => {
        if (owned(event.detail.ctx)) error();
    });
    hydrate();
})();
