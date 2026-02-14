import threading
import json
from flask import Flask, render_template_string, jsonify
from loguru import logger
from datetime import datetime

data_lock = threading.Lock()
_account_manager = None

shared_context = {
    "streamers": {},
    "points": {},
    "last_update": {},
    "status": "Initializing",
    "stream_status": {}
}

app = Flask(__name__)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KICKMINER</title>
<style>
:root {
    --kick-green: #53fc18;
    --kick-green-dim: rgba(83, 252, 24, 0.15);
    --kick-green-border: rgba(83, 252, 24, 0.3);
    --bg-dark: #0b0e11;
    --bg-card: #191c21;
    --bg-card-hover: #1e2228;
    --bg-header: #12151a;
    --border-color: #2a2e35;
    --text-primary: #efeff1;
    --text-secondary: #adadb8;
    --text-muted: #7a7a85;
    --red: #f04747;
    --orange: #faa61a;
    --blue: #5865f2;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
    background: var(--bg-dark);
    color: var(--text-primary);
    min-height: 100vh;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

.header {
    text-align: center;
    padding: 32px 0 24px;
}

.header h1 {
    font-size: 36px;
    font-weight: 800;
    letter-spacing: 2px;
}

.header .kick-text {
    color: var(--kick-green);
}

.header .subtitle {
    color: var(--text-muted);
    font-size: 13px;
    margin-top: 4px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.summary-bar {
    display: flex;
    justify-content: center;
    gap: 32px;
    padding: 16px 24px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}

.summary-item {
    text-align: center;
}

.summary-item .value {
    font-size: 24px;
    font-weight: 700;
    color: var(--kick-green);
}

.summary-item .label {
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 2px;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}

.status-active {
    background: var(--kick-green-dim);
    color: var(--kick-green);
    border: 1px solid var(--kick-green-border);
}

.status-init {
    background: rgba(250, 166, 26, 0.15);
    color: var(--orange);
    border: 1px solid rgba(250, 166, 26, 0.3);
}

.status-dot-pulse {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

.account-section {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    margin-bottom: 20px;
    overflow: hidden;
    transition: border-color 0.2s;
}

.account-section:hover {
    border-color: #3a3e45;
}

.account-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: var(--bg-header);
    border-bottom: 1px solid var(--border-color);
    flex-wrap: wrap;
    gap: 12px;
}

.account-name {
    font-size: 18px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 8px;
}

.account-name .alias {
    color: var(--kick-green);
}

.account-meta {
    display: flex;
    gap: 20px;
    font-size: 13px;
    color: var(--text-secondary);
    flex-wrap: wrap;
}

.account-meta .meta-item {
    display: flex;
    align-items: center;
    gap: 4px;
}

.streamer-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 12px;
    padding: 16px;
}

.streamer-card {
    background: var(--bg-dark);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 14px 16px;
    position: relative;
    transition: all 0.2s;
    overflow: hidden;
}

.streamer-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: var(--border-color);
    transition: background 0.2s;
}

.streamer-card.watching::before { background: var(--kick-green); }
.streamer-card.online::before { background: var(--orange); }
.streamer-card.offline::before { background: #444; }

.streamer-card:hover {
    background: var(--bg-card-hover);
    border-color: #3a3e45;
}

.card-row-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.streamer-info-left {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
}

.s-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

.s-dot.watching {
    background: var(--kick-green);
    box-shadow: 0 0 8px rgba(83, 252, 24, 0.5);
    animation: pulse 2s infinite;
}

.s-dot.online { background: var(--orange); }
.s-dot.offline { background: #555; }

.s-name {
    font-weight: 600;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.s-name a {
    color: var(--text-primary);
    text-decoration: none;
    transition: color 0.2s;
}

.s-name a:hover {
    color: var(--kick-green);
}

.s-priority {
    font-size: 10px;
    background: #2a2e35;
    color: var(--text-muted);
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 600;
    flex-shrink: 0;
}

.s-errors {
    font-size: 10px;
    background: rgba(240, 71, 71, 0.15);
    color: var(--red);
    padding: 2px 6px;
    border-radius: 4px;
    flex-shrink: 0;
}

.card-row-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.s-points {
    font-size: 18px;
    font-weight: 700;
    color: var(--kick-green);
}

.s-time {
    font-size: 11px;
    color: var(--text-muted);
}

.watch-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 11px;
    font-weight: 600;
    transition: all 0.2s;
    flex-shrink: 0;
}

.watch-btn:hover {
    border-color: var(--kick-green);
    color: var(--kick-green);
    background: var(--kick-green-dim);
}

.watch-btn svg {
    width: 12px;
    height: 12px;
}

.s-status-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.s-status-label.watching { color: var(--kick-green); }
.s-status-label.online { color: var(--orange); }
.s-status-label.offline { color: var(--text-muted); }

.grand-total {
    text-align: center;
    padding: 24px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    margin: 24px 0;
}

.grand-total .label {
    color: var(--text-muted);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.grand-total .value {
    font-size: 40px;
    font-weight: 800;
    color: var(--kick-green);
    margin-top: 4px;
}

.footer {
    text-align: center;
    padding: 16px 0 24px;
    color: var(--text-muted);
    font-size: 12px;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
}

.refresh-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--kick-green);
    animation: pulse 2s infinite;
}

.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}

.empty-state .icon { font-size: 48px; margin-bottom: 12px; }
.empty-state .text { font-size: 16px; }

@media (max-width: 600px) {
    .header h1 { font-size: 28px; }
    .summary-bar { gap: 16px; padding: 12px 16px; }
    .summary-item .value { font-size: 18px; }
    .streamer-grid { grid-template-columns: 1fr; }
    .account-header { padding: 12px 16px; }
    .account-meta { gap: 12px; }
}
</style>
</head>
<body>
<div class="container">

    <div class="header">
        <h1><span class="kick-text">KICK</span>MINER</h1>
        <div class="subtitle">Channel Points Farmer</div>
    </div>

    <div class="summary-bar" id="summary-bar">
        <div class="summary-item">
            <div class="value" id="sum-status">—</div>
            <div class="label">Status</div>
        </div>
        <div class="summary-item">
            <div class="value" id="sum-accounts">0</div>
            <div class="label">Accounts</div>
        </div>
        <div class="summary-item">
            <div class="value" id="sum-watching">0</div>
            <div class="label">Watching</div>
        </div>
        <div class="summary-item">
            <div class="value" id="sum-online">0</div>
            <div class="label">Online</div>
        </div>
        <div class="summary-item">
            <div class="value" id="sum-total">0</div>
            <div class="label">Total Points</div>
        </div>
    </div>

    <div id="accounts-container">
        <div class="empty-state">
            <div class="icon">⏳</div>
            <div class="text">Connecting to streamers...</div>
        </div>
    </div>

    <div class="grand-total">
        <div class="label">Grand Total Points</div>
        <div class="value" id="grand-total">0</div>
    </div>

    <div class="footer">
        <span class="refresh-dot"></span>
        <span>Auto-refresh every 5s · Last update: <span id="refresh-time">--:--:--</span></span>
    </div>

</div>

<script>
const EXTERNAL_LINK_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>';

function fmtTime(v) {
    if (!v || v === "N/A" || v === "None" || v === "null") return "—";
    try {
        if (v.includes("T")) return new Date(v).toLocaleTimeString();
        return v;
    } catch(e) { return v; }
}

function fmtNumber(n) {
    return (n || 0).toLocaleString();
}

function renderAccounts(data) {
    const container = document.getElementById("accounts-container");
    const accounts = data.accounts || [];

    if (!accounts.length) {
        renderLegacy(data);
        return;
    }

    let html = "";
    let grandTotal = 0;
    let totalWatching = 0;
    let totalOnline = 0;

    accounts.forEach((acc, idx) => {
        const alias = acc.alias || ("Account " + (idx+1));
        const proxy = acc.proxy;
        const active = acc.active_count || 0;
        const limit = acc.max_concurrent || 0;
        const streamers = acc.streamers || {};
        const order = acc.streamer_order || Object.keys(streamers);

        let accTotal = 0;
        let accWatching = 0;
        let accOnline = 0;
        let cards = "";

        order.forEach(name => {
            const info = streamers[name] || {};
            const pts = info.points || 0;
            accTotal += pts;

            let cardClass = "offline";
            let dotClass = "offline";
            let statusText = "OFFLINE";

            if (info.watching) {
                cardClass = "watching";
                dotClass = "watching";
                statusText = "WATCHING";
                accWatching++;
            } else if (info.online) {
                cardClass = "online";
                dotClass = "online";
                statusText = "QUEUED";
                accOnline++;
            }

            const errHtml = info.errors > 0
                ? '<span class="s-errors">⚠ ' + info.errors + '</span>'
                : "";

            const lastUp = fmtTime(info.last_update);
            const pri = info.priority !== undefined ? info.priority : "?";

            cards += '<div class="streamer-card ' + cardClass + '">' +
                '<div class="card-row-top">' +
                    '<div class="streamer-info-left">' +
                        '<span class="s-dot ' + dotClass + '"></span>' +
                        '<span class="s-name"><a href="https://kick.com/' + name + '" target="_blank">' + name + '</a></span>' +
                        '<span class="s-priority">#' + pri + '</span>' +
                        errHtml +
                    '</div>' +
                    '<a href="https://kick.com/' + name + '" target="_blank" class="watch-btn">' +
                        EXTERNAL_LINK_SVG + ' Watch' +
                    '</a>' +
                '</div>' +
                '<div class="card-row-bottom">' +
                    '<span class="s-points">' + fmtNumber(pts) + ' pts</span>' +
                    '<div>' +
                        '<span class="s-status-label ' + cardClass + '">' + statusText + '</span>' +
                        ' <span class="s-time">' + lastUp + '</span>' +
                    '</div>' +
                '</div>' +
            '</div>';
        });

        grandTotal += accTotal;
        totalWatching += accWatching;
        totalOnline += accOnline;

        const proxyHtml = proxy ? "🔒 Proxy" : "🌐 Direct";

        html += '<div class="account-section">' +
            '<div class="account-header">' +
                '<div class="account-name">' +
                    '<span class="alias">' + alias + '</span>' +
                '</div>' +
                '<div class="account-meta">' +
                    '<span class="meta-item">' + proxyHtml + '</span>' +
                    '<span class="meta-item">👁 ' + active + '/' + limit + '</span>' +
                    '<span class="meta-item" style="color:var(--kick-green)">💰 ' + fmtNumber(accTotal) + '</span>' +
                '</div>' +
            '</div>' +
            '<div class="streamer-grid">' + cards + '</div>' +
        '</div>';
    });

    container.innerHTML = html;
    document.getElementById("grand-total").textContent = fmtNumber(grandTotal);

    document.getElementById("sum-accounts").textContent = accounts.length;
    document.getElementById("sum-watching").textContent = totalWatching;
    document.getElementById("sum-online").textContent = totalOnline + totalWatching;
    document.getElementById("sum-total").textContent = fmtNumber(grandTotal);

    const st = data.status || "Active";
    const statusEl = document.getElementById("sum-status");
    if (st === "Active") {
        statusEl.innerHTML = '<span class="status-badge status-active"><span class="status-dot-pulse"></span>Active</span>';
    } else {
        statusEl.innerHTML = '<span class="status-badge status-init">' + st + '</span>';
    }
}

function renderLegacy(data) {
    const container = document.getElementById("accounts-container");
    const streamers = data.streamers || {};
    const points = data.points || {};
    const names = Object.keys(streamers);

    if (!names.length) {
        container.innerHTML = '<div class="empty-state"><div class="icon">📡</div><div class="text">No streamers configured</div></div>';
        return;
    }

    let html = '<div class="streamer-grid">';
    let total = 0;

    names.forEach(name => {
        const pts = points[name] || 0;
        total += pts;
        const status = (data.stream_status || {})[name] || "offline";
        const cardClass = status === "online" ? "watching" : "offline";
        const dotClass = cardClass;
        const lastUp = (data.last_update || {})[name] || "—";

        html += '<div class="streamer-card ' + cardClass + '">' +
            '<div class="card-row-top">' +
                '<div class="streamer-info-left">' +
                    '<span class="s-dot ' + dotClass + '"></span>' +
                    '<span class="s-name"><a href="https://kick.com/' + name + '" target="_blank">' + name + '</a></span>' +
                '</div>' +
                '<a href="https://kick.com/' + name + '" target="_blank" class="watch-btn">' +
                    EXTERNAL_LINK_SVG + ' Watch</a>' +
            '</div>' +
            '<div class="card-row-bottom">' +
                '<span class="s-points">' + fmtNumber(pts) + ' pts</span>' +
                '<span class="s-time">' + lastUp + '</span>' +
            '</div>' +
        '</div>';
    });

    html += '</div>';
    container.innerHTML = html;
    document.getElementById("grand-total").textContent = fmtNumber(total);
    document.getElementById("sum-total").textContent = fmtNumber(total);
    document.getElementById("sum-watching").textContent =
        names.filter(n => (data.stream_status||{})[n] === "online").length;
}

function refresh() {
    fetch("/api/data")
        .then(r => r.json())
        .then(data => {
            renderAccounts(data);
            document.getElementById("refresh-time").textContent =
                new Date().toLocaleTimeString();
        })
        .catch(err => console.error("Refresh error:", err));
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>
"""


@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/data')
def get_data():
    global _account_manager

    if _account_manager is not None:
        try:
            accounts_status = _account_manager.get_all_status()

            flat_streamers = {}
            flat_points = {}
            flat_last_update = {}
            flat_stream_status = {}

            for acc in accounts_status:
                alias = acc.get("alias", "")
                for name, info in acc.get("streamers", {}).items():
                    if name not in flat_streamers:
                        flat_streamers[name] = alias
                    flat_points[name] = info.get("points", 0)
                    lu = info.get("last_update")
                    flat_last_update[name] = lu if lu else "N/A"

                    if info.get("watching"):
                        flat_stream_status[name] = "online"
                    elif info.get("online"):
                        flat_stream_status[name] = "online"
                    else:
                        flat_stream_status[name] = "offline"

            return jsonify({
                "streamers": flat_streamers,
                "points": flat_points,
                "last_update": flat_last_update,
                "status": "Active",
                "stream_status": flat_stream_status,
                "accounts": accounts_status,
            })

        except Exception as e:
            logger.error(f"API /api/data error: {e}")
            return jsonify({
                "streamers": {}, "points": {},
                "last_update": {}, "status": "Error",
                "stream_status": {}, "accounts": [],
            })
    else:
        with data_lock:
            clean_lu = {}
            for k, v in shared_context["last_update"].items():
                clean_lu[k] = (
                    v.strftime("%H:%M:%S")
                    if isinstance(v, datetime) else str(v)
                )
            return jsonify({
                "streamers": shared_context["streamers"],
                "points": shared_context["points"],
                "last_update": clean_lu,
                "status": shared_context["status"],
                "stream_status": shared_context["stream_status"],
                "accounts": [],
            })


@app.route('/api/accounts')
def get_accounts():
    global _account_manager
    if _account_manager is not None:
        try:
            return jsonify(_account_manager.get_all_status())
        except Exception as e:
            logger.error(f"API /api/accounts error: {e}")
    return jsonify([])


def start_server(streamers_data, port=5000):
    global _account_manager

    if hasattr(streamers_data, 'get_all_status'):
        _account_manager = streamers_data
        with data_lock:
            names = _account_manager.get_all_streamers_flat()
            shared_context["streamers"] = {s: "" for s in names}
            shared_context["points"] = {s: 0 for s in names}
            shared_context["last_update"] = {s: "N/A" for s in names}
            shared_context["stream_status"] = {s: "offline" for s in names}
            shared_context["status"] = "Active"
    elif isinstance(streamers_data, list):
        with data_lock:
            shared_context["streamers"] = {s: "" for s in streamers_data}
            shared_context["points"] = {s: 0 for s in streamers_data}
            shared_context["last_update"] = {s: "N/A" for s in streamers_data}
            shared_context["stream_status"] = {s: "offline" for s in streamers_data}
            shared_context["status"] = "Active"
    elif isinstance(streamers_data, dict):
        with data_lock:
            shared_context["streamers"] = streamers_data
            shared_context["status"] = "Active"

    def run():
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        logger.info(f"🌍 Web Dashboard available at http://localhost:{port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

    threading.Thread(target=run, daemon=True).start()


def update_streamer_info(name, points, last_update_time,
                         stream_id=None, account_alias=None):
    with data_lock:
        shared_context["points"][name] = points
        shared_context["last_update"][name] = last_update_time
        if account_alias:
            shared_context["streamers"][name] = account_alias
        shared_context["stream_status"][name] = (
            "online" if stream_id else "offline"
        )