/* ============================================================================
 * File Path: quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/quan_ly_lich_su_cuon.js
 * Chuc nang: Mac dinh neo day khi co tin nhan moi, va kich hoat tai lai lich su
 *            cu khi nguoi dung keo thanh cuon cham dinh khung hoi thoai.
 * File lien quan: hien_thi_hoi_thoai.js, khoi_tao_ung_dung.js
 * ============================================================================ */

export function tao_bo_dieu_khien_cuon({
    khung_cuon,
    nut_ve_cuoi,
    nhan_trang_thai_tai,
    khi_tai_lich_su_cu,
}) {
    let tu_dong_neo_day = true;
    let dang_tai_lich_su = false;
    let da_het_lich_su_cu = false;

    function cuon_xuong_day_ngay() {
        tu_dong_neo_day = true;
        khung_cuon.scrollTop = khung_cuon.scrollHeight;
        nut_ve_cuoi.style.display = "none";
    }

    function neo_day_neu_dang_o_cuoi() {
        if (tu_dong_neo_day) {
            requestAnimationFrame(() => {
                khung_cuon.scrollTop = khung_cuon.scrollHeight;
                nut_ve_cuoi.style.display = "none";
            });
        } else {
            nut_ve_cuoi.style.display = "inline-flex";
        }
    }

    async function xu_ly_khi_cuon() {
        const khoang_cach_day = khung_cuon.scrollHeight - khung_cuon.clientHeight - khung_cuon.scrollTop;
        tu_dong_neo_day = khoang_cach_day <= 48;
        nut_ve_cuoi.style.display = tu_dong_neo_day ? "none" : "inline-flex";

        // Khi keo len sat dinh (<= 16px) thi tai lai lich su cu hon va giu vi tri cuon
        if (khung_cuon.scrollTop <= 16 && !dang_tai_lich_su && !da_het_lich_su_cu) {
            dang_tai_lich_su = true;
            nhan_trang_thai_tai.textContent = "Đang tải lại lịch sử cũ hơn...";

            const chieu_cao_truoc = khung_cuon.scrollHeight;
            const vi_tri_cuon_truoc = khung_cuon.scrollTop;

            const co_them_du_lieu = await khi_tai_lich_su_cu();
            if (!co_them_du_lieu) {
                da_het_lich_su_cu = true;
                nhan_trang_thai_tai.textContent = "Đã hiển thị toàn bộ lịch sử lưu trữ";
            } else {
                nhan_trang_thai_tai.textContent = "Đã nạp thêm lịch sử · Kéo lên đỉnh để tải tiếp";
                requestAnimationFrame(() => {
                    const chieu_cao_sau = khung_cuon.scrollHeight;
                    khung_cuon.scrollTop = chieu_cao_sau - chieu_cao_truoc + vi_tri_cuon_truoc;
                });
            }
            dang_tai_lich_su = false;
        }
    }

    khung_cuon.addEventListener("scroll", xu_ly_khi_cuon, { passive: true });
    nut_ve_cuoi.addEventListener("click", cuon_xuong_day_ngay);

    return {
        cuon_xuong_day_ngay,
        neo_day_neu_dang_o_cuoi,
        dat_lai_trang_thai_lich_su() {
            da_het_lich_su_cu = false;
            nhan_trang_thai_tai.textContent = "Kéo lên sát đỉnh khung chat để tải lại lịch sử cũ hơn";
        },
    };
}