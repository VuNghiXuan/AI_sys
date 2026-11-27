/* ============================================================================
 * File Path: chat_ui/static/chat_ui/js/telemetry.js
 * Module: Bo Ve Tinh Telemetry Va Bieu Do Thoi Gian Thuc
 * Linked Files: templates/chat_ui/partials/telemetry_panel.html,
 *               static/chat_ui/js/workbench.js
 * Purpose: Cap nhat RAM/CPU/Token/Model dang chay, ve bieu do sparkline nhay
 *          lien tuc va doc so do phan cung thuc neu endpoint tra ve.
 * ============================================================================ */

(() => {
    const SAMPLE_LEN = 32;
    const state = {
        isRunning: false,
        ramPct: 52,
        cpuPct: 14,
        tokPerSec: 0,
        ramSeries: Array(SAMPLE_LEN).fill(52),
        cpuSeries: Array(SAMPLE_LEN).fill(14),
        tokSeries: Array(SAMPLE_LEN).fill(0),
        activeModel: "--",
        activeProvider: "",
    };

    function el(id) {
        return document.getElementById(id);
    }

    function pushSample(arr, val) {
        const clamped = Math.max(0, Math.min(100, Number(val) || 0));
        arr.push(clamped);
        if (arr.length > SAMPLE_LEN) arr.shift();
    }

    function drawLineChart(canvasId, series, strokeColor) {
        const canvas = el(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const w = canvas.clientWidth || 260;
        const h = canvas.height || 36;
        if (canvas.width !== w) canvas.width = w;

        ctx.clearRect(0, 0, w, h);
        ctx.strokeStyle = "#e2e8f0";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, h / 2);
        ctx.lineTo(w, h / 2);
        ctx.stroke();

        if (!series.length) return;
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        series.forEach((v, idx) => {
            const x = (idx / Math.max(1, series.length - 1)) * (w - 4) + 2;
            const y = h - 4 - (v / 100) * (h - 8);
            if (idx === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();
    }

    function renderHardware() {
        const ramBar = el("ramMeterFill");
        const cpuBar = el("cpuMeterFill");
        const ramTxt = el("hwRamSummary");
        const cpuTxt = el("hwCpuSummary");

        if (ramBar) ramBar.style.width = `${state.ramPct.toFixed(0)}%`;
        if (cpuBar) cpuBar.style.width = `${state.cpuPct.toFixed(0)}%`;
        if (ramTxt && !ramTxt.dataset.locked) {
            ramTxt.textContent = `${state.ramPct.toFixed(0)}%`;
        }
        if (cpuTxt) cpuTxt.textContent = `${state.cpuPct.toFixed(0)}%`;

        drawLineChart("ramSparkCanvas", state.ramSeries, "#0284c7");
        drawLineChart("cpuSparkCanvas", state.cpuSeries, "#0d9488");
    }

    function renderTokenRate() {
        const rateLbl = el("tokRateBadge");
        if (rateLbl) rateLbl.textContent = `${state.tokPerSec.toFixed(1)} tok/s`;

        const normalized = Math.min(100, (state.tokPerSec / 60) * 100);
        const copy = [...state.tokSeries.slice(1), normalized];
        state.tokSeries = copy;
        drawLineChart("tokenFlowCanvas", state.tokSeries, "#d97706");
    }

    function setRunningState(running, modelName = "", providerName = "") {
        state.isRunning = Boolean(running);
        if (modelName) state.activeModel = modelName;
        if (providerName) state.activeProvider = providerName;

        const topModel = el("topActiveModel");
        if (topModel) {
            topModel.textContent = state.isRunning
                ? `Đang chạy: ${state.activeModel}`
                : `Model: ${state.activeModel}`;
        }

        const modeBadge = el("providerChainBadge");
        if (modeBadge) modeBadge.textContent = state.isRunning ? "RUNNING" : "IDLE";

        document.querySelectorAll("[data-provider-row]").forEach((row) => {
            const pName = row.getAttribute("data-provider-row");
            const badge = row.querySelector("[data-prov-status]");
            const active = state.isRunning && pName === state.activeProvider;
            row.classList.toggle("is-active", active);
            if (badge) {
                badge.textContent = active ? "Đang chạy" : "Chờ";
            }
        });
    }

    function applyServerTelemetry(payload = {}) {
        const hw = payload.phan_cung || payload.hardware || null;
        if (hw) {
            if (typeof hw.ram_su_dung_phan_tram === "number") {
                state.ramPct = hw.ram_su_dung_phan_tram;
            } else if (hw.tong_ram_mb && hw.ram_kha_dung_mb != null) {
                state.ramPct = ((hw.tong_ram_mb - hw.ram_kha_dung_mb) / hw.tong_ram_mb) * 100;
            }
            const ramTxt = el("hwRamSummary");
            if (ramTxt && hw.ram_kha_dung_mb != null && hw.tong_ram_mb != null) {
                ramTxt.textContent = `${hw.ram_kha_dung_mb}/${hw.tong_ram_mb} MB (${state.ramPct.toFixed(0)}%)`;
                ramTxt.dataset.locked = "1";
            }
            const cpuCores = el("hwCpuCoresBadge");
            if (cpuCores && hw.cpu_logic) cpuCores.textContent = `${hw.cpu_logic} CPU`;
        }

        const tok = payload.token || {};
        const tIn = tok.input ?? tok.tong_input ?? 0;
        const tOut = tok.output ?? tok.tong_output ?? 0;
        const tSum = tok.tong ?? (tIn + tOut);

        if (el("tokInputVal")) el("tokInputVal").textContent = String(tIn);
        if (el("tokOutputVal")) el("tokOutputVal").textContent = String(tOut);
        if (el("tokTotalVal")) el("tokTotalVal").textContent = String(tSum);
        if (el("topTokensBadge")) el("topTokensBadge").textContent = `${tSum} tok`;

        const warns = Array.isArray(payload.canh_bao) ? payload.canh_bao.length : 0;
        if (el("telemWarnCount")) el("telemWarnCount").textContent = `${warns} CẢNH BÁO`;

        const modelText = payload.model || payload.tier || payload.provider || "--";
        setRunningState(false, modelText, payload.provider || "");
    }

    function tick() {
        if (state.isRunning) {
            const jitterCpu = (Math.random() - 0.35) * 16;
            state.cpuPct = Math.max(8, Math.min(98, state.cpuPct + jitterCpu));
            const jitterRam = (Math.random() - 0.45) * 4;
            state.ramPct = Math.max(10, Math.min(96, state.ramPct + jitterRam));
            state.tokPerSec = Math.max(4, 18 + (Math.random() - 0.3) * 24);
        } else {
            state.cpuPct = Math.max(3, Math.min(35, state.cpuPct + (Math.random() - 0.5) * 3));
            state.tokPerSec = Math.max(0, state.tokPerSec * 0.5);
        }

        pushSample(state.ramSeries, state.ramPct);
        pushSample(state.cpuSeries, state.cpuPct);
        renderHardware();
        renderTokenRate();
    }

    async function pollRealTelemetry() {
        const endpoint = document.body.dataset.telemetryUrl;
        if (!endpoint) return;
        try {
            const res = await fetch(endpoint, { headers: { "X-Requested-With": "XMLHttpRequest" } });
            if (!res.ok) return;
            const data = await res.json();
            if (typeof data.cpu_percent === "number") state.cpuPct = data.cpu_percent;
            if (typeof data.ram_percent === "number") state.ramPct = data.ram_percent;
            renderHardware();
        } catch (_) {
            // Bỏ qua nếu chưa cấu hình endpoint polling riêng
        }
    }

    window.WorkbenchTelemetry = {
        setRunningState,
        applyServerTelemetry,
    };

    setInterval(tick, 750);
    setInterval(pollRealTelemetry, 3000);
    tick();
})();