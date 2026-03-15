(function () {
    'use strict';

    var form = document.getElementById('dcf-form');
    var resultsSection = document.getElementById('results');
    var errorSection = document.getElementById('error');
    var errorMessage = document.getElementById('error-message');
    var summaryGrid = document.getElementById('summary-grid');
    var resultsBody = document.getElementById('results-body');
    var runBtn = document.getElementById('run-btn');

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

    function makeSummaryItem(label, value, cls) {
        var div = document.createElement('div');
        div.className = 'summary-item';
        if (cls) div.classList.add(cls);

        var lbl = document.createElement('div');
        lbl.className = 'summary-label';
        lbl.textContent = label;
        div.appendChild(lbl);

        var val = document.createElement('div');
        val.className = 'summary-value';
        val.textContent = value;
        div.appendChild(val);

        return div;
    }

    function showResults(data) {
        errorSection.classList.add('hidden');
        resultsSection.classList.remove('hidden');

        var lastYear = data.years[data.years.length - 1];

        // Summary panel
        summaryGrid.innerHTML = '';
        summaryGrid.appendChild(makeSummaryItem('Enterprise Value', fmtCurrency(data.enterprise_value), 'summary-primary'));
        summaryGrid.appendChild(makeSummaryItem('Y5 Revenue', fmtCurrency(lastYear.revenue)));
        summaryGrid.appendChild(makeSummaryItem('Y5 Free Cash Flow', fmtCurrency(lastYear.fcf)));
        summaryGrid.appendChild(makeSummaryItem('Discount Rate', fmtPct(data.params.discount_rate)));

        // Detail table
        resultsBody.innerHTML = '';
        for (var i = 0; i < data.years.length; i++) {
            var y = data.years[i];
            var tr = document.createElement('tr');

            var cells = [
                { text: 'Y' + y.year, cls: '' },
                { text: fmtCurrencyTable(y.revenue), cls: 'num' },
                { text: fmtCurrencyTable(y.fcf), cls: 'num' },
                { text: fmtFactor(y.discount_factor), cls: 'num dim' },
                { text: fmtCurrencyTable(y.pv_fcf), cls: 'num' }
            ];

            for (var j = 0; j < cells.length; j++) {
                var td = document.createElement('td');
                td.className = cells[j].cls;
                td.textContent = cells[j].text;
                tr.appendChild(td);
            }

            resultsBody.appendChild(tr);
        }
    }

    function showError(msg) {
        resultsSection.classList.add('hidden');
        errorSection.classList.remove('hidden');
        errorMessage.textContent = msg;
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        var payload = {
            revenue_prev: parseFloat(document.getElementById('revenue_prev').value),
            revenue_growth: parseFloat(document.getElementById('revenue_growth').value),
            margin: parseFloat(document.getElementById('margin').value),
            discount_rate: parseFloat(document.getElementById('discount_rate').value)
        };

        runBtn.disabled = true;
        runBtn.textContent = 'Running...';

        fetch('/run-dcf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(function (res) {
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
        })
        .then(function (data) {
            showResults(data);
        })
        .catch(function (err) {
            showError(String(err.message || err));
        })
        .finally(function () {
            runBtn.disabled = false;
            runBtn.textContent = 'Run Model';
        });
    });
})();
