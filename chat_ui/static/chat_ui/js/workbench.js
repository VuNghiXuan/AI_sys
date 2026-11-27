/* ============================================================================
 * File Path: chat_ui/static/chat_ui/js/workbench.js
 * Module: Dieu Phoi Giao Dien Chat, Tab Co Dinh, Sidebar Va Hieu Ung Go Chu
 * Linked Files: templates/chat_ui/layout/base.html,
 *               templates/chat_ui/layout/index.html,
 *               static/chat_ui/js/telemetry.js
 * Purpose: Xu ly thu gon sidebar, chuyen tab co dinh, gui prompt toi api_chat,
 *          hien trang thai chay song dong va stream chu muot ma.
 * ============================================================================ */

(() => {
    let isBusy = false;
    let abortCtrl = null;
    let elapsedInterval = null;
    let startTimeMs = 0;

    function byId(id) {
        return document.getElementById(id);
    }

    function getCsrfToken() {
        const el = document.querySelector("[name=csrfmiddlewaretoken]");
        return el ? el.value : "";
    }

    function bindSidebarToggle() {
        const btn = byId("btnToggleSidebar");
        const grid = byId("workbenchGrid");
        if (!btn || !grid) return;

        btn.addEventListener("click", () => {
            const collapsed = grid.classList.toggle("sidebar-collapsed");
            btn.textContent = collapsed ? "☰ Mở rộng" : "☰ Thu gọn";
        });
    }

    function bindStickyTabs() {
        const buttons = document.querySelectorAll("[data-wb-tab]");
        const panels = document.querySelectorAll("[data-wb-panel]");
        buttons.forEach((btn) => {
            btn.addEventListener("click", () => {
                const target = btn.getAttribute("data-wb-tab");
                buttons.forEach((b) => b.classList.toggle("active", b === btn));
                panels.forEach((p) => p.classList.toggle("active", p.id === target));
            });
        });
    }

    function appendPromptBubble(text) {
        const feed = byId("chatFeed");
        if (!feed) return;
        const item = document.createElement("div");
        item.className = "chat-item is-prompt";
        item.innerHTML = `
      <div class="chat-meta">
        <span class="chat-role-badge">BẠN • PROMPT</span>
        <span>${new Date().toLocaleTimeString("vi-VN")}</span>
      </div>
      <div class="chat-bubble"></div>
    `;
        item.querySelector(".chat-bubble").textContent = text;
        feed.appendChild(item);
        const panel = byId("wb-tab-chat");
        if (panel) panel.scrollTop = panel.scrollHeight;
    }

    function createReplyBubble(metaLabel = "SYSTEM") {
        const feed = byId("chatFeed");
        const item = document.createElement("div");
        item.className = "chat-item is-reply";
        item.innerHTML = `
      <div class="chat-meta">
        <span class="chat-role-badge">TRẢ LỜI</span>
        <span data-reply-meta>${metaLabel}</span>
      </div>
      <div class="chat-bubble typing-cursor" data-reply-body></div>
    `;
        feed.appendChild(item);
        const panel = byId("wb-tab-chat");
        if (panel) panel.scrollTop = panel.scrollHeight;
        return {
            bodyEl: item.querySelector("[data-reply-body]"),
            metaEl: item.querySelector("[data-reply-meta]"),
        };
    }

    function streamText(bodyEl, fullText, onDone) {
        const text = String(fullText || "");
        if (!text) {
            bodyEl.classList.remove("typing-cursor");
            if (onDone) onDone();
            return;
        }

        const stepSize = text.length > 1500 ? 20 : text.length > 500 ? 9 : 3;
        let idx = 0;

        function step() {
            idx = Math.min(text.length, idx + stepSize);
            bodyEl.textContent = text.slice(0, idx);
            const panel = byId("wb-tab-chat");
            if (panel) panel.scrollTop = panel.scrollHeight;

            if (idx < text.length) {
                requestAnimationFrame(step);
            } else {
                bodyEl.classList.remove("typing-cursor");
                if (onDone) onDone();
            }
        }
        requestAnimationFrame(step);
    }

    function setBusy(busy, stepMsg = "", modelName = "", providerName = "") {
        isBusy = busy;
        const badge = byId("globalRunStatus");
        const strip = byId("liveStatusBanner");
        const stepLbl = byId("liveStepText");
        const modelLbl = byId("liveModelText");
        const timerLbl = byId("liveElapsedText");
        const btnSend = byId("btnSendPrompt");
        const btnStop = byId("btnStopRun");

        if (badge) {
            badge.textContent = busy ? "Đang chạy" : "Hoàn tất";
            badge.classList.toggle("is-running", busy);
        }
        if (strip) strip.classList.toggle("is-hidden", !busy);
        if (stepLbl && stepMsg) stepLbl.textContent = stepMsg;
        if (modelLbl) modelLbl.textContent = modelName ? `Model: ${modelName}` : "Model: đang định tuyến";
        if (btnSend) btnSend.disabled = busy;
        if (btnStop) btnStop.classList.toggle("is-hidden", !busy);

        if (window.WorkbenchTelemetry) {
            window.WorkbenchTelemetry.setRunningState(busy, modelName, providerName);
        }

        clearInterval(elapsedInterval);
        if (busy) {
            startTimeMs = performance.now();
            elapsedInterval = setInterval(() => {
                const sec = ((performance.now() - startTimeMs) / 1000).toFixed(1);
                if (timerLbl) timerLbl.textContent = `${sec}s`;
                if (byId("topLatencyBadge")) byId("topLatencyBadge").textContent = `${sec}s`;
            }, 100);
        }
    }

    async function handleSendPrompt(event) {
        event.preventDefault();
        if (isBusy) return;

        const input = byId("promptInput");
        const allowWrite = byId("allowWriteCheck");
        const promptText = (input ? input.value : "").trim();
        if (!promptText) return;

        const selector = byId("profileSelector");
        const profile = selector ? selector.value : "quality_first_free_first";
        const apiUrl = document.body.dataset.chatApiUrl || "/api/chat/";

        input.value = "";
        appendPromptBubble(promptText);
        const reply = createReplyBubble(`Profile: ${profile}`);
        setBusy(true, "Đang quét ngữ cảnh & điều phối model...", profile, "local_ollama");

        abortCtrl = new AbortController();

        try {
            const res = await fetch(apiUrl, {
                method: "POST",
                signal: abortCtrl.signal,
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: JSON.stringify({
                    prompt: promptText,
                    ghi_tep: Boolean(allowWrite && allowWrite.checked),
                    profile,
                }),
            });

            const data = await res.json();
            if (!res.ok && !data.noi_dung) {
                throw new Error(data.error || `HTTP ${res.status}`);
            }

            if (data.profile && byId("topProfileName")) {
                byId("topProfileName").textContent = data.profile;
            }

            const content = data.noi_dung || data.reply || data.message || JSON.stringify(data, null, 2);
            const modelUsed = data.provider || data.tier || data.profile || profile;

            setBusy(true, "Đang hiển thị phản hồi...", modelUsed, data.provider || "");
            streamText(reply.bodyEl, content, () => {
                if (reply.metaEl) {
                    reply.metaEl.textContent = `${data.che_do || "gateway"} • ${modelUsed}`;
                }
                if (window.WorkbenchTelemetry) {
                    window.WorkbenchTelemetry.applyServerTelemetry(data);
                }
                setBusy(false, "Hoàn tất", modelUsed, data.provider || "");
            });
        } catch (err) {
            const msg = err.name === "AbortError" ? "Đã dừng tác vụ theo yêu cầu." : `Lỗi: ${err.message}`;
            reply.bodyEl.textContent = msg;
            reply.bodyEl.classList.remove("typing-cursor");
            setBusy(false, "Đã dừng / Lỗi", "--", "");
        }
    }

    function bindComposer() {
        const form = byId("chatPromptForm");
        const textarea = byId("promptInput");
        const btnStop = byId("btnStopRun");

        if (form) form.addEventListener("submit", handleSendPrompt);

        if (textarea) {
            textarea.addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.altKey && !e.shiftKey) {
                    e.preventDefault();
                    if (form) form.requestSubmit();
                }
            });
        }

        if (btnStop) {
            btnStop.addEventListener("click", () => {
                if (abortCtrl) abortCtrl.abort();
            });
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        bindSidebarToggle();
        bindStickyTabs();
        bindComposer();
    });
})();