(function () {
    'use strict';

    var buildBtn = document.getElementById('build-btn');
    var buildContent = document.getElementById('build-content');
    var releaseContent = document.getElementById('release-content');
    var runtimeMeta = document.getElementById('runtime-meta');
    var runtimeContent = document.getElementById('runtime-content');
    var worksheetHeading = document.getElementById('worksheet-heading');
    var worksheetContainer = document.getElementById('worksheet-container');
    var errorSection = document.getElementById('error');
    var errorMessage = document.getElementById('error-message');

    // ── Formatters ──

    function fmtCurrency(n) {
        return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function fmtCurrencyTable(n) {
        return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function fmtPct(n) {
        return (n * 100).toFixed(1) + '%';
    }

    function fmtFactor(n) {
        return n.toFixed(4);
    }

    function fmtTime(iso) {
        if (!iso) return '—';
        return iso.replace('T', ' ').replace('+00:00', ' UTC');
    }

    // ── Helpers ──

    function clearError() {
        errorSection.classList.add('hidden');
    }

    function showError(msg) {
        errorSection.classList.remove('hidden');
        errorMessage.textContent = msg;
    }

    function api(method, path, body) {
        var opts = { method: method, headers: {} };
        if (body) {
            opts.headers['Content-Type'] = 'application/json';
            opts.body = JSON.stringify(body);
        }
        return fetch(path, opts).then(function (res) {
            if (!res.ok) {
                return res.json()
                    .catch(function () { throw new Error('Request failed (' + res.status + ')'); })
                    .then(function (err) {
                        var msg = err.detail;
                        if (Array.isArray(msg)) msg = msg.map(function (e) { return e.msg; }).join('; ');
                        throw new Error(msg || 'Request failed (' + res.status + ')');
                    });
            }
            return res.json();
        });
    }

    function getParams() {
        return {
            revenue_prev: parseFloat(document.getElementById('revenue_prev').value),
            revenue_growth: parseFloat(document.getElementById('revenue_growth').value),
            margin: parseFloat(document.getElementById('margin').value),
            discount_rate: parseFloat(document.getElementById('discount_rate').value)
        };
    }

    // ── Section renderers ──

    function showBuild(data) {
        buildContent.innerHTML =
            '<div class="meta-block">' +
                '<span class="status-badge status-draft">draft</span>' +
                '<span class="meta-line">Hash: <span class="hash">sha256:' + data.content_hash + '</span></span>' +
                '<span class="meta-line">Built: ' + fmtTime(data.built_at) + '</span>' +
                '<span class="meta-line">EV: ' + fmtCurrency(data.results.enterprise_value) + '</span>' +
            '</div>' +
            '<button id="release-btn" class="btn-release">Release to Prod</button>';

        document.getElementById('release-btn').addEventListener('click', doRelease);
    }

    function showRelease(data) {
        releaseContent.innerHTML =
            '<div class="meta-block">' +
                '<span class="status-badge status-released">released</span>' +
                '<span class="meta-line">Version: v' + data.version + '</span>' +
                '<span class="meta-line">Hash: <span class="hash">sha256:' + data.content_hash + '</span></span>' +
                '<span class="meta-line">Released: ' + fmtTime(data.released_at) + '</span>' +
            '</div>';
    }

    function showRuntimeMeta(rel) {
        runtimeMeta.innerHTML =
            '<div class="runtime-meta-strip">' +
                '<span>v' + rel.version + '</span>' +
                '<span class="meta-sep">·</span>' +
                '<span class="hash">sha256:' + rel.content_hash + '</span>' +
                '<span class="meta-sep">·</span>' +
                '<span>Built ' + fmtTime(rel.built_at) + '</span>' +
                '<span class="meta-sep">·</span>' +
                '<span>Released ' + fmtTime(rel.released_at) + '</span>' +
            '</div>';
    }

    function showRuntime(data) {
        var lastYear = data.years[data.years.length - 1];

        var html =
            '<div class="summary-grid">' +
                summaryItem('Enterprise Value', fmtCurrency(data.enterprise_value), true) +
                summaryItem('Y5 Revenue', fmtCurrency(lastYear.revenue)) +
                summaryItem('Y5 Free Cash Flow', fmtCurrency(lastYear.fcf)) +
                summaryItem('Discount Rate', fmtPct(data.params.discount_rate)) +
            '</div>' +
            '<p class="table-caption">Yearly projection</p>' +
            '<table><thead><tr>' +
                '<th>Year</th><th class="num">Revenue ($)</th><th class="num">FCF ($)</th>' +
                '<th class="num">Discount Factor</th><th class="num">PV of FCF ($)</th>' +
            '</tr></thead><tbody>';

        for (var i = 0; i < data.years.length; i++) {
            var y = data.years[i];
            html += '<tr>' +
                '<td>Y' + y.year + '</td>' +
                '<td class="num">' + fmtCurrencyTable(y.revenue) + '</td>' +
                '<td class="num">' + fmtCurrencyTable(y.fcf) + '</td>' +
                '<td class="num dim">' + fmtFactor(y.discount_factor) + '</td>' +
                '<td class="num">' + fmtCurrencyTable(y.pv_fcf) + '</td>' +
            '</tr>';
        }

        html += '</tbody></table>' +
            '<p class="result-note">5-year projection only. No terminal value included.</p>';

        runtimeContent.innerHTML = html;
    }

    function summaryItem(label, value, primary) {
        return '<div class="summary-item' + (primary ? ' summary-primary' : '') + '">' +
            '<div class="summary-label">' + label + '</div>' +
            '<div class="summary-value">' + value + '</div>' +
        '</div>';
    }

    function renderWorksheet() {
        worksheetHeading.classList.add('hidden');
        worksheetContainer.innerHTML = '';
        api('GET', '/artifact/released')
            .then(function (ws) {
                worksheetHeading.classList.remove('hidden');
                WorksheetViewer.render(worksheetContainer, ws);
            })
            .catch(function () { /* no artifact yet — leave empty */ });
    }

    // ── Actions ──

    function doBuild() {
        clearError();
        buildBtn.disabled = true;
        buildBtn.textContent = 'Building...';

        api('POST', '/build', getParams())
            .then(function (data) {
                showBuild(data);
            })
            .catch(function (err) { showError(err.message); })
            .finally(function () {
                buildBtn.disabled = false;
                buildBtn.textContent = 'Build Artifact';
            });
    }

    function doRelease() {
        clearError();
        var btn = document.getElementById('release-btn');
        if (btn) { btn.disabled = true; btn.textContent = 'Releasing...'; }

        api('POST', '/release')
            .then(function (data) {
                showRelease(data);
                showRuntimeMeta(data);
                return api('POST', '/run');
            })
            .then(function (data) {
                showRuntime(data);
                renderWorksheet();
            })
            .catch(function (err) { showError(err.message); });
    }

    // ── Page load: hydrate from server state ──

    function hydrate() {
        api('GET', '/state')
            .then(function (state) {
                if (state.draft) showBuild(state.draft);
                if (state.released) {
                    showRelease(state.released);
                    showRuntimeMeta(state.released);
                    showRuntime(state.released.results);
                    renderWorksheet();
                }
            })
            .catch(function () { /* ignore — fresh state */ });
    }

    // ── Bind ──

    buildBtn.addEventListener('click', doBuild);
    hydrate();
})();
