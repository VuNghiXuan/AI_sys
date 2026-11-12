/**
 * File: enterprise_factory/static/enterprise_factory/js/war_room.js
 * Quản lý logic Alpine.js cho vnxBox Live War Room (Verbose Debugging Edition)
 */

function warRoom() {
    return {
        socket: null,
        statusText: 'Đang kết nối WebSocket...',
        directiveText: '',
        loading: false,
        agents: [],
        discussions: [],
        logs: [],
        patches: [],

        showMentionMenu: false,
        mentionFilter: '',
        cursorPosition: 0,

        init() {
            console.log("[*] [WarRoom] Khởi tạo giao diện Live War Room chuẩn Enterprise...");
            this.loadInitialData();
            this.initWebSocket();
        },

        // 🛡️ Helper định danh chuẩn xác: Phân định rạch ròi User (Sếp) và AI Agent
        isUserMessage(senderName, messageContent = '') {
            const sender = String(senderName || '').trim().toUpperCase();
            const content = String(messageContent || '').trim();

            // 1. Nếu sender chứa tên rõ ràng của bất kỳ Agent AI nào -> CHẮC CHẮN LÀ AI (Nằm lề trái, KHÔNG BAO GIỜ là User)
            if (sender.includes('BOD') || sender.includes('DEV') || sender.includes('HR') ||
                sender.includes('QA') || sender.includes('AI') || sender.includes('HỆ THỐNG') ||
                sender.includes('MANAGER_01') || sender.includes('CEO_01')) {
                return false;
            }

            // 2. Nếu sender chứa tên tường minh của Sếp -> CHẮC CHẮN LÀ SẾP (Nằm lề phải)
            if (sender.includes('SẾP VŨ') || sender.includes('VŨ') || sender === 'USER') {
                return true;
            }

            // 3. Nếu sender bị rỗng (""), ta kiểm tra xem có phải nội dung trả lời từ AI hay không
            // Lưu ý: Tuyệt đối không dựa vào việc có chữ "Sếp Vũ" trong nội dung để kết luận là User, vì AI chào Sếp cũng chứa từ này!
            if (content.startsWith('Xin chào') ||
                content.startsWith('Xin lỗi') ||
                content.startsWith('Dạ') ||
                content.startsWith('📊') ||
                content.includes('tôi là một trợ lý') ||
                content.includes('tập đoàn có') ||
                content.includes('nhân sự lập trình') ||
                content.includes('tôi đã nhận được chỉ đạo')) {
                return false; // Là AI -> Nằm lề trái
            }

            // 4. Còn lại các lệnh gọi ngắn của Sếp (như "alo", "@BOD_CEO_01", "@HR_MANAGER_01") -> Nằm lề phải
            return true;
        },

        // 1. Tải dữ liệu ban đầu từ Backend
        async loadInitialData() {
            console.log("[*] [HTTP INIT] Đang tải dữ liệu ban đầu từ /api/war-room/init-data/...");
            try {
                const response = await fetch('/api/war-room/init-data/');
                if (response.ok) {
                    const data = await response.json();
                    console.log("[*] [HTTP INIT SUCCESS] Dữ liệu nhận từ DB:", data);

                    this.agents = (data.agents || []).map(agent => ({
                        ...agent,
                        role_type: agent.role_type ? String(agent.role_type).toUpperCase() : 'GENERAL'
                    }));

                    // Chuẩn hóa toàn bộ lịch sử cũ từ DB
                    this.discussions = (data.discussions || []).map(item => {
                        let sender = item.agent_name || item.sender || '';
                        const isUser = this.isUserMessage(sender, item.message_content);

                        if (isUser) {
                            sender = 'Sếp Vũ';
                        } else if (!sender || sender.trim() === '') {
                            // Nếu là AI nhưng thiếu tên, dò nội dung để gán đúng tên nhân sự
                            const content = item.message_content || '';
                            if (content.includes('tuyển dụng') || content.includes('nhân sự')) {
                                sender = 'HR Director (Giám Đốc Nhân Sự AI)';
                            } else {
                                sender = 'BOD CEO (Tổng Giám Đốc AI)';
                            }
                        }

                        return {
                            ...item,
                            agent_name: sender
                        };
                    });

                    this.patches = data.patches || [];
                } else {
                    console.warn("[!] [HTTP INIT WARNING] Response không OK:", response.status);
                }
            } catch (e) {
                console.error("[!] [HTTP INIT ERROR] Không thể tải dữ liệu init qua HTTP:", e);
                this.agents = [
                    { agent_id: 'BOD_CEO_01', display_name: 'Giám đốc Điều hành', role_type: 'BOD' },
                    { agent_id: 'DEV_BE_01', display_name: 'Kỹ sư Backend Core', role_type: 'DEV_BE' },
                    { agent_id: 'HR_MANAGER_01', display_name: 'Giám đốc Nhân sự', role_type: 'HR' }
                ];
            }
        },

        // 2. Khởi tạo kết nối WebSocket Real-time
        initWebSocket() {
            const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
            const wsUrl = wsScheme + '://' + window.location.host + '/ws/war-room/';
            console.log(`[*] [WS] Đang kết nối WebSocket tới: ${wsUrl}`);

            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                console.log("[+] [WS OPEN] Kết nối WebSocket thành công!");
                this.statusText = '● Trực tuyến (Connected)';
            };

            this.socket.onmessage = (event) => {
                console.log("[INCOMING WS EVENT RAW] ->", event.data);
                try {
                    const data = JSON.parse(event.data);
                    if (data.status === 'broadcast') {
                        console.log(`[WS BROADCAST] Sender: "${data.sender}" | Target: "${data.target}" | Phase: "${data.phase}" | Content: "${data.content}"`);

                        if (data.phase === 'DIRECTIVE' || data.phase === 'GENERAL' || data.phase.includes('QUERY') || data.phase.includes('DEBATE')) {
                            this.logs.push({
                                time: new Date().toLocaleTimeString(),
                                text: `[${data.sender} -> ${data.target}] (${data.phase}): ${data.content}`
                            });
                        }

                        if (data.content) {
                            let sender = data.sender;
                            if (this.isUserMessage(sender)) {
                                sender = 'Sếp Vũ';
                            }
                            console.log(`[WS RENDER] Thêm message vào UI | Sender hiển thị: "${sender}"`);
                            this.discussions.unshift({
                                id: Date.now() + Math.random(),
                                agent_name: sender,
                                message_content: data.content,
                                created_at: new Date().toLocaleTimeString()
                            });
                        }
                    }
                } catch (parseErr) {
                    console.error("[!] [WS PARSE ERROR] Không thể parse JSON từ WS:", parseErr);
                }
            };

            this.socket.onclose = (closeEvent) => {
                console.warn("[-] [WS CLOSE] Mất kết nối WebSocket. Code:", closeEvent.code);
                this.statusText = '✕ Mất kết nối (Disconnected)';
                setTimeout(() => this.initWebSocket(), 3000);
            };

            this.socket.onerror = (err) => {
                console.error("[!] [WS ERROR]", err);
                this.statusText = '⚠ Lỗi kết nối WebSocket';
            };
        },

        insertMention(agentId) {
            this.directiveText = `@${agentId} ${this.directiveText}`;
            this.showMentionMenu = false;
            const inputEl = document.querySelector('input[type="text"]');
            if (inputEl) inputEl.focus();
        },

        sendDirective() {
            if (!this.directiveText.trim()) return;

            this.loading = true;
            const text = this.directiveText;
            console.log(`[*] [SEND DIRECTIVE] Gửi lệnh: "${text}"`);

            let target = 'ALL';
            if (text.includes('@all')) {
                target = 'ALL';
            } else {
                const match = text.match(/@([A-Za-z0-9_]+)/);
                if (match) {
                    target = match[1];
                }
            }
            console.log(`[*] [SEND DIRECTIVE] Target Agent được phân rã: "${target}"`);

            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({
                    action: 'chat',
                    message: text,
                    target_agent: target
                }));
                this.directiveText = '';
            } else {
                console.error("[!] [SEND ERROR] WebSocket chưa sẵn sàng!");
                alert("WebSocket chưa sẵn sàng kết nối!");
            }

            this.loading = false;
        },

        async approvePatch(patchId) {
            console.log(`[*] [PATCH] Phê duyệt patch #${patchId}`);
            alert(`Đang phê duyệt bản vá #${patchId}...`);
        },

        async rejectPatch(patchId) {
            console.log(`[*] [PATCH] Từ chối patch #${patchId}`);
            this.patches = this.patches.filter(p => p.id !== patchId);
        },

        checkMention(event) {
            const val = this.directiveText;
            const lastChar = val.slice(-1);
            if (lastChar === '@' || (val.includes('@') && !val.slice(val.lastIndexOf('@')).includes(' '))) {
                this.showMentionMenu = true;
            } else {
                this.showMentionMenu = false;
            }
        },

        selectMention(mentionTag) {
            this.directiveText = this.directiveText.replace(/@[^\s]*$/, '') + mentionTag + ' ';
            this.showMentionMenu = false;
            const inputEl = document.querySelector('input[type="text"]');
            if (inputEl) inputEl.focus();
        },

        // 🛡️ Hiển thị tên chuẩn xác trên khung chat
        getSenderLabel(senderName) {
            if (this.isUserMessage(senderName)) {
                return 'Sếp Vũ';
            }
            return senderName || 'BOD CEO AI';
        },

        // 🎨 Phân màu sắc huy hiệu cực kỳ chi tiết cho từng loại Agent AI
        getAgentBadgeClass(senderName) {
            if (!senderName) return 'bg-slate-800 text-slate-300 border-slate-700';
            const name = String(senderName).toUpperCase();

            // 1. Ban Giám Đốc / BOD / CEO -> Đỏ quyền lực
            if (name.includes('BOD') || name.includes('CEO') || name.includes('GIÁM ĐỐC ĐIỀU HÀNH')) {
                return 'bg-red-950 text-red-300 border-red-800';
            }
            // 2. Nhân sự / HR -> Tím thủy chung
            else if (name.includes('HR') || name.includes('NHÂN SỰ') || name.includes('RECRUITMENT')) {
                return 'bg-purple-950 text-purple-300 border-purple-800';
            }
            // 3. Kỹ thuật / Dev / Backend -> Xanh dương
            else if (name.includes('DEV') || name.includes('KỸ SƯ') || name.includes('BACKEND') || name.includes('ENGINEER')) {
                return 'bg-blue-950 text-blue-300 border-blue-800';
            }
            // 4. Kiểm định / QA / Test -> Xanh ngọc / Emerald
            else if (name.includes('QA') || name.includes('TEST') || name.includes('KIỂM ĐỊNH')) {
                return 'bg-emerald-950 text-emerald-300 border-emerald-800';
            }

            // Mặc định cho các Agent khác hoặc Hệ thống -> Xám chuyên nghiệp
            return 'bg-slate-800 text-slate-300 border-slate-700';
        },
    }
}