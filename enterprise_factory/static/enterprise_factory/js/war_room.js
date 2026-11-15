/* ==========================================================================
   Đường dẫn: enterprise_factory/static/enterprise_factory/js/war_room.js
   Chức năng: vnxBox Enterprise War Room (Bản chuẩn tối ưu Singleton WebSocket & Chống trùng lặp init)
   ========================================================================== */

function warRoomMaster() {
    return {
        // --- 1. State Chat & WebSocket ---
        messages: [],
        discussions: [],
        agents: [],
        directiveText: '',
        inputMessage: '',
        loading: false,
        isThinking: false,
        showMentionMenu: false,
        mentionFilter: '',
        statusText: 'Đang kết nối WebSocket...',
        socket: null,
        isWsConnected: false,
        isConnecting: false,
        reconnectTimer: null,
        isInitialized: false, // Cờ chống gọi init() 2 lần

        // --- 2. State Progress & Terminal ---
        isProgressActive: false,
        currentProgressText: 'Sẵn sàng...',
        progressLogs: [],
        hideTimeout: null,
        openTerminal: false,
        progressInitialized: false,

        // --- 3. State Dynamic Matrix & Patches ---
        dynamicTools: [],
        dynamicWorkflows: [],
        patches: [],
        isMatrixLoaded: false,

        // --- INIT CHUNG ---
        init() {
            if (this.isInitialized) {
                console.warn("[!] [war_room.js] Bỏ qua init() trùng lặp.");
                return;
            }
            this.isInitialized = true;

            console.log("[*] [war_room.js] Khởi tạo toàn diện vnxBox Enterprise War Room...");
            this.loadInitData();
            this.connectWebSocket();
            this.initProgressEvents();
        },

        // --- TẢI DỮ LIỆU KHỞI TẠO ---
        loadInitData() {
            console.log("[*] Đang gọi API /api/war-room/init-data/...");
            fetch('/api/war-room/init-data/')
                .then(res => res.json())
                .then(data => {
                    console.log("[+] Dữ liệu init-data nhận được:", data);

                    if (data.agents && Array.isArray(data.agents)) {
                        this.agents = data.agents.map(a => ({
                            agent_id: a.agent_id || '',
                            display_name: a.display_name || 'AI Agent',
                            title_name: a.title_name || 'Chuyên gia AI',
                            role_type: a.role_type || 'GENERAL',
                            avatar_url: a.avatar_url || '',
                            domain_scope: a.domain_scope || ''
                        }));
                        console.log(`[+] Đã nạp ${this.agents.length} nhân sự vào sidebar.`);
                    }

                    if (data.discussions && Array.isArray(data.discussions)) {
                        this.messages = data.discussions;
                        this.discussions = data.discussions;
                        console.log(`[+] Đã nạp toàn bộ ${this.discussions.length} tin nhắn lịch sử vào khung chat.`);
                    }

                    this.dynamicTools = data.tools || [];
                    this.dynamicWorkflows = data.workflows || [];
                    this.isMatrixLoaded = true;
                })
                .catch(err => {
                    console.error("❌ Lỗi tải dữ liệu init-data:", err);
                });
        },

        // --- WEBSOCKET CHAT & PROGRESS (SINGLETON) ---
        connectWebSocket() {
            if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
                console.log("[*] WebSocket đang hoạt động, bỏ qua lệnh mở trùng.");
                return;
            }

            if (this.socket) {
                try {
                    this.socket.onclose = null;
                    this.socket.onerror = null;
                    this.socket.close();
                } catch (e) { }
                this.socket = null;
            }

            const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
            const wsUrl = `${wsScheme}://${window.location.host}/ws/war-room/`;

            console.log(`[*] Thiết lập kết nối WebSocket tới: ${wsUrl}`);
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                console.log("[+] WebSocket đã kết nối ổn định.");
                this.isWsConnected = true;
                this.statusText = '🟢 Đã kết nối Live War Room';
                if (this.reconnectTimer) {
                    clearTimeout(this.reconnectTimer);
                    this.reconnectTimer = null;
                }
            };

            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log("[WS INCOMING]:", data);
                    this.handleIncomingMessage(data);
                } catch (e) {
                    console.error("❌ Lỗi parse JSON từ WebSocket:", e);
                }
            };

            this.socket.onclose = (event) => {
                console.warn(`[-] WebSocket ngắt kết nối (Code: ${event.code}).`);
                this.isWsConnected = false;
                this.socket = null;

                if (!this.reconnectTimer) {
                    this.reconnectTimer = setTimeout(() => {
                        this.reconnectTimer = null;
                        this.connectWebSocket();
                    }, 3000);
                }
            };

            this.socket.onerror = (err) => {
                console.error("[-] Lỗi sự kiện WebSocket:", err);
                this.isWsConnected = false;
            };
        },

        // --- GỬI CHỈ ĐẠO ---
        sendDirective() {
            const text = (this.directiveText || this.inputMessage || '').trim();
            if (!text) return;

            if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
                this.statusText = '🟡 Đang kết nối lại...';
                this.connectWebSocket();
                setTimeout(() => {
                    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                        this.executeSendPayload(text);
                    } else {
                        alert("⚠️ Không thể kết nối tới WebSocket Server!");
                    }
                }, 800);
                return;
            }

            this.executeSendPayload(text);
        },

        executeSendPayload(text) {
            const payload = {
                action: 'chat',
                message: text,
                target_agent: 'ALL'
            };

            this.socket.send(JSON.stringify(payload));

            const userItem = {
                id: Date.now() + Math.random(),
                sender: 'Sếp Vũ',
                agent_name: 'Sếp Vũ',
                title_name: 'Chủ sở hữu hệ thống',
                message_content: text,
                sender_type: 'USER',
                created_at: new Date().toLocaleTimeString()
            };

            this.discussions.unshift(userItem);
            this.messages = this.discussions;

            this.directiveText = '';
            this.inputMessage = '';
            this.showMentionMenu = false;
            this.loading = true;
            this.isThinking = true;
        },

        sendMessage() {
            this.sendDirective();
        },

        // --- @MENTION ---
        checkMention(event) {
            const val = event.target.value;
            const cursorIdx = event.target.selectionStart;
            const textBeforeCursor = val.substring(0, cursorIdx);
            const match = textBeforeCursor.match(/@(\w*)$/);

            if (match) {
                this.showMentionMenu = true;
                this.mentionFilter = match[1].toLowerCase();
            } else {
                this.showMentionMenu = false;
            }
        },

        selectMention(mentionCode) {
            const val = this.directiveText;
            const lastAtIdx = val.lastIndexOf('@');
            if (lastAtIdx !== -1) {
                this.directiveText = val.substring(0, lastAtIdx) + `${mentionCode} `;
            } else {
                this.directiveText += `${mentionCode} `;
            }
            this.showMentionMenu = false;
            const inputEl = document.querySelector('input[x-model="directiveText"]');
            if (inputEl) inputEl.focus();
        },

        insertMention(agentId) {
            this.directiveText = `@${agentId} ${this.directiveText}`;
            const inputEl = document.querySelector('input[x-model="directiveText"]');
            if (inputEl) inputEl.focus();
        },

        // --- RENDER HELPERS ---
        isUserMessage(item) {
            if (!item) return false;
            const senderType = String(item.sender_type || '').toUpperCase();
            const senderName = String(item.agent_name || item.sender || '').toLowerCase();
            return senderType === 'USER' || senderName.includes('vũ') || senderName.includes('sếp');
        },

        getSenderLabel(item) {
            if (typeof item === 'string') return item;
            return item.agent_name || item.sender || 'AI Expert';
        },

        getAgentBadgeClass(agentName) {
            const name = String(agentName || '').toUpperCase();
            if (name.includes('BOD') || name.includes('CEO')) return 'bg-red-950 text-red-300 border-red-800';
            if (name.includes('DEV') || name.includes('CODE')) return 'bg-blue-950 text-blue-300 border-blue-800';
            if (name.includes('HR')) return 'bg-purple-950 text-purple-300 border-purple-800';
            if (name.includes('QA') || name.includes('SEARCH') || name.includes('TEST')) return 'bg-emerald-950 text-emerald-300 border-emerald-800';
            return 'bg-slate-800 text-slate-300 border-slate-700';
        },

        // --- SELF-LEARNING FEEDBACK ---
        sendFeedback(item, feedbackType) {
            console.log(`[*] Gửi feedback [${feedbackType}] cho tin nhắn ID: ${item.id || 'N/A'}`);
            const payload = {
                message_id: item.id || null,
                agent_name: item.agent_name || item.sender,
                content: item.message_content,
                feedback_type: feedbackType
            };

            fetch('/api/war-room/feedback/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(payload)
            })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        console.log(`✅ Đã ghi nhận phản hồi [${feedbackType}] thành công!`);
                    }
                })
                .catch(err => {
                    console.warn("ℹ️ [Feedback Note]: " + err.message);
                });
        },

        getCsrfToken() {
            const name = 'csrftoken';
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },

        // --- PROGRESS & TERMINAL ---
        initProgressEvents() {
            if (this.progressInitialized) return;
            this.progressInitialized = true;

            window.addEventListener('toggle-terminal', () => {
                this.openTerminal = !this.openTerminal;
            });
        },

        handleProgressEvent(data) {
            if (data.phase && data.phase !== 'GENERAL') {
                this.isProgressActive = true;
                this.currentProgressText = data.content || 'Đang xử lý nghiệp vụ...';
                this.pushLog(data.content);

                if (this.hideTimeout) clearTimeout(this.hideTimeout);
                this.hideTimeout = setTimeout(() => {
                    this.isProgressActive = false;
                }, 12000);
            }
        },

        pushLog(text) {
            this.progressLogs.unshift({
                id: Date.now() + Math.random(),
                timestamp: new Date().toLocaleTimeString(),
                text: text
            });
            if (this.progressLogs.length > 100) this.progressLogs.pop();
        },

        clearLogs() {
            this.progressLogs = [];
            this.isProgressActive = false;
        },

        // --- XỬ LÝ TIN NHẮN TỪ WEBSOCKET ---
        handleIncomingMessage(data) {
            if (data.content && (data.sender_type === 'AGENT' || data.sender_type === 'SYSTEM')) {
                const newItem = {
                    id: Date.now() + Math.random(),
                    sender: data.sender || 'AI Expert',
                    agent_name: data.sender || 'AI Expert',
                    title_name: data.title_name || 'Chuyên gia AI',
                    message_content: data.content,
                    sender_type: data.sender_type,
                    created_at: new Date().toLocaleTimeString()
                };

                this.discussions.unshift(newItem);
                this.messages = this.discussions;

                this.loading = false;
                this.isThinking = false;
            }

            this.handleProgressEvent(data);
        }
    }
}