// File: static/enterprise_factory/js/war_room.js
document.addEventListener('alpine:init', () => {
    Alpine.data('enterpriseApp', () => ({
        agents: [],
        discussions: [],
        patches: [],
        directiveText: '',
        selectedCompany: 'GLOBAL',
        loading: false,

        // --- CÁC BIẾN QUẢN LÝ SMART POLLING (NGỦ ĐÔNG THÔNG MINH) ---
        pollInterval: 3000, // Mặc định 3 giây
        idleTimer: 0,       // Bộ đếm thời gian rảnh rỗi

        init() {
            this.fetchState();
            // Bắt đầu chạy vòng lặp thông minh
            this.scheduleNextPoll();
        },

        // Vòng lặp đệ quy thông minh thay thế setInterval cứng nhắc
        scheduleNextPoll() {
            setTimeout(async () => {
                await this.fetchState();
                // Lên lịch gọi tiếp theo với tốc độ hiện tại (có thể đã giãn ra nếu rảnh)
                this.scheduleNextPoll();
            }, this.pollInterval);
        },

        async fetchState() {
            try {
                let res = await fetch('/api/viber/state/');
                let data = await res.json();
                if (data.status === 'success') {
                    this.agents = data.agents;
                    this.discussions = data.discussions;
                    this.patches = data.patches;

                    // --- LOGIC TỰ ĐỘNG ĐIỀU CHỈNH NHỊP QUÉT ---
                    let hasPending = this.patches && this.patches.some(p => p.status === 'PENDING');

                    if (!hasPending && !this.loading) {
                        this.idleTimer += this.pollInterval;
                        // Nếu im lặng quá 45 giây không có patch chờ hay AI đang chạy -> Giãn nhịp lên 10 giây tiết kiệm CPU
                        if (this.idleTimer > 45000) {
                            this.pollInterval = 10000;
                        }
                    } else {
                        // Có việc bận (có patch chờ hoặc đang xử lý) -> Đưa về tốc độ real-time 3 giây ngay lập tức
                        this.wakeUpFast();
                    }
                }
            } catch (err) {
                console.error("Lỗi đồng bộ trạng thái phòng họp:", err);
            }
        },

        // Hàm đánh thức hệ thống chạy max speed ngay lập tức
        wakeUpFast() {
            this.pollInterval = 3000;
            this.idleTimer = 0;
        },

        async sendDirective() {
            if (!this.directiveText.trim() || this.loading) return;

            // Đánh thức ngay khi Sếp ra lệnh
            this.wakeUpFast();

            let text = this.directiveText;
            this.directiveText = '';
            this.loading = true;

            try {
                let res = await fetch('/api/viber/execute/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        directive_text: text,
                        company_code: this.selectedCompany
                    })
                });
                let data = await res.json();
                if (data.status === 'success') {
                    await this.fetchState();
                } else {
                    alert('Lỗi xử lý: ' + data.message);
                }
            } catch (err) {
                console.error("Lỗi khi gửi chỉ đạo:", err);
            } finally {
                this.loading = false;
            }
        },

        async approvePatch(patchId) {
            if (!confirm("Sếp có chắc chắn muốn duyệt và áp dụng bản vá code này vào hệ thống?")) return;

            // Đánh thức ngay khi Sếp tương tác duyệt patch
            this.wakeUpFast();

            try {
                let res = await fetch('/api/viber/approve/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ patch_id: patchId })
                });
                let data = await res.json();
                if (data.status === 'success') {
                    alert(data.message);
                    await this.fetchState();
                } else {
                    alert('Lỗi duyệt patch: ' + data.message);
                }
            } catch (err) {
                console.error("Lỗi khi duyệt patch:", err);
            }
        },

        // Thêm hàm từ chối / hủy patch đã hoàn thiện
        async rejectPatch(patchId) {
            if (!confirm(`Sếp có chắc chắn muốn hủy bản vá ID #${patchId} này không?`)) return;

            this.wakeUpFast();

            try {
                let res = await fetch('/api/viber/reject/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ patch_id: patchId })
                });
                let data = await res.json();
                if (data.status === 'success') {
                    await this.fetchState();
                } else {
                    alert('Lỗi hủy patch: ' + data.message);
                }
            } catch (err) {
                console.error('Lỗi kết nối khi hủy patch:', err);
            }
        }
    }));
});