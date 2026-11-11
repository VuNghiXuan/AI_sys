/**
 * File: enterprise_factory/static/enterprise_factory/js/war_room.js
 * Quản lý logic Alpine.js cho vnxBox Live War Room (WebSocket, @ Mention, Live Status Feed)
 */

function warRoom() {
    return {
        socket: null,
        statusText: 'Đang kết nối WebSocket...',
        directiveText: '',
        loading: false,
        agents: [],        // Danh sách nhân sự lấy từ DB
        discussions: [],   // Lịch sử thảo luận từ DB
        logs: [],          // Log WebSocket thời gian thực
        patches: [],       // Bản vá code chờ duyệt

        // Cấu hình popup @ Mention - Khai báo rõ ràng tại đây để Alpine.js nhận diện
        showMentionMenu: false,
        mentionFilter: '',
        cursorPosition: 0,

        init() {
            console.log("[*] [WarRoom] Khởi tạo giao diện Live War Room...");
            this.loadInitialData();
            this.initWebSocket();
        },

        // 1. Tải dữ liệu ban đầu từ Backend (Agents & Discussions)
        async loadInitialData() {
            try {
                const response = await fetch('/api/war-room/init-data/');
                if (response.ok) {
                    const data = await response.json();

                    // Chuẩn hóa tuyệt đối role_type thành string uppercase để tránh lỗi .includes()
                    this.agents = (data.agents || []).map(agent => ({
                        ...agent,
                        role_type: agent.role_type ? String(agent.role_type).toUpperCase() : 'GENERAL'
                    }));

                    this.discussions = data.discussions || [];
                    this.patches = data.patches || [];
                }
            } catch (e) {
                console.warn("[!] [WarRoom] Không thể tải dữ liệu init qua HTTP (Dùng mock hoặc chạy qua WS):", e);
                // Dữ liệu fallback chuẩn an toàn
                this.agents = [
                    { agent_id: 'BOD_CEO_01', display_name: 'Giám đốc Điều hành', role_type: 'BOD' },
                    { agent_id: 'DEV_BE_01', display_name: 'Kỹ sư Backend Core', role_type: 'DEV_BE' },
                    { agent_id: 'HR_MANAGER_01', display_name: 'Giám đốc Nhân sự', role_type: 'HR' },
                    { agent_id: 'QA_TESTER_01', display_name: 'Kiểm định Chất lượng', role_type: 'QA' }
                ];
            }
        },

        // 2. Khởi tạo kết nối WebSocket Real-time
        initWebSocket() {
            const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
            const wsUrl = wsScheme + '://' + window.location.host + '/ws/war-room/';

            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                this.statusText = '● Trực tuyến (Connected)';
                console.log("[+] [WebSocket] Đã kết nối thành công tới vnxBox Core ASGI.");
            };

            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log("[*] [WebSocket] Nhận message:", data);

                if (data.status === 'broadcast') {
                    this.logs.push({
                        time: new Date().toLocaleTimeString(),
                        text: `[${data.sender} -> ${data.target}] (${data.phase}): ${data.content}`
                    });

                    if (data.content) {
                        this.discussions.unshift({
                            id: Date.now(),
                            agent_name: data.sender,
                            message_content: data.content,
                            created_at: new Date().toLocaleTimeString()
                        });
                    }
                }
            };

            this.socket.onclose = () => {
                this.statusText = '✕ Mất kết nối (Disconnected)';
                console.warn("[!] [WebSocket] Đã đóng kết nối. Đang thử kết nối lại sau 3s...");
                setTimeout(() => this.initWebSocket(), 3000);
            };

            this.socket.onerror = (err) => {
                this.statusText = '⚠ Lỗi kết nối WebSocket';
                console.error("[-] [WebSocket Error]:", err);
            };
        },

        // 3. Click vào nhân sự ở Sidebar để tự động chèn @mention vào ô input
        insertMention(agentId) {
            this.directiveText = `@${agentId} ${this.directiveText}`;
            this.showMentionMenu = false;
            const inputEl = document.querySelector('input[type="text"]');
            if (inputEl) inputEl.focus();
        },

        // 4. Gửi chỉ đạo qua WebSocket
        sendDirective() {
            if (!this.directiveText.trim()) return;

            this.loading = true;
            const text = this.directiveText;

            let target = 'ALL';
            if (text.includes('@all')) {
                target = 'ALL';
            } else {
                const match = text.match(/@([A-Za-z0-9_]+)/);
                if (match) {
                    target = match[1];
                }
            }

            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({
                    action: 'chat',
                    message: text,
                    target_agent: target
                }));

                this.discussions.unshift({
                    id: Date.now(),
                    agent_name: 'Sếp Vũ',
                    message_content: text,
                    created_at: new Date().toLocaleTimeString()
                });

                this.directiveText = '';
            } else {
                alert("WebSocket chưa sẵn sàng kết nối. Vui lòng kiểm tra lại server Daphne!");
            }

            this.loading = false;
        },

        // Phê duyệt bản vá code (Approve Patch)
        async approvePatch(patchId) {
            alert(`Đang phê duyệt bản vá #${patchId}...`);
        },

        // Hủy bản vá code
        async rejectPatch(patchId) {
            this.patches = this.patches.filter(p => p.id !== patchId);
        },

        // 5. Kiểm tra ký tự '@' để hiển thị menu Popup Mention
        checkMention(event) {
            const val = this.directiveText;
            const lastChar = val.slice(-1);
            if (lastChar === '@' || (val.includes('@') && !val.slice(val.lastIndexOf('@')).includes(' '))) {
                this.showMentionMenu = true;
            } else {
                this.showMentionMenu = false;
            }
        },

        // 6. Chọn nhân sự từ menu Popup Mention
        selectMention(mentionTag) {
            this.directiveText = this.directiveText.replace(/@[^\s]*$/, '') + mentionTag + ' ';
            this.showMentionMenu = false;
            const inputEl = document.querySelector('input[type="text"]');
            if (inputEl) inputEl.focus();
        }
    }
}