/* ============================================================================
 * File Path: quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/xu_ly_da_y_dinh.js
 * Chuc nang: Tach nhieu y dinh (multi-intent) trong 1 prompt thanh cac nhanh
 *            co thu tu va gop phan hoi ro rang theo tung nhanh.
 * File lien quan: khoi_tao_ung_dung.js, dong_ho_va_nhip_ollama.js
 * ============================================================================ */

export function tach_cac_nhanh_tu_prompt(noi_dung_prompt) {
    const van_ban = String(noi_dung_prompt || "").trim();
    if (!van_ban) return [];

    const cac_phan = van_ban
        .split(/(?:\r?\n)+|[.;!?]+|\b(?:roi|rồi|sau do|sau đó|dong thoi|đồng thời|kem theo|kèm theo)\b/gi)
        .map((item) => item.trim().replace(/^[\s,:-]+|[\s,:-]+$/g, ""))
        .filter((item) => item.length >= 2);

    const danh_sach_tho = cac_phan.length ? cac_phan : [van_ban];

    return danh_sach_tho.map((noi_dung, chi_so) => {
        const thuong = noi_dung.toLowerCase();
        let ma_nhom = "phan_tich_nghiep_vu";
        let ten_nhom = "Phân tích nghiệp vụ";
        let model_goi_y = "qwen2.5:3b";

        if (/\b(code|ham|hàm|class|file|model|api|sql|db|loi|lỗi|fix|sua|sửa)\b/.test(thuong)) {
            ma_nhom = "xu_ly_ky_thuat";
            ten_nhom = "Xử lý kỹ thuật & Code";
            model_goi_y = "qwen2.5-coder:7b";
        } else if (/\b(tra cuu|tra cứu|tim kiem|tìm kiếm|quy dinh|quy định|luat|luật)\b/.test(thuong)) {
            ma_nhom = "tra_cuu_thong_tin";
            ten_nhom = "Tra cứu thông tin";
            model_goi_y = "qwen2.5:3b";
        }

        return {
            so_nhanh: chi_so + 1,
            noi_dung,
            ma_nhom,
            ten_nhom,
            model_goi_y,
        };
    });
}

export function chon_model_cho_cac_nhanh(cac_nhanh, tong_do_dai_prompt) {
    const co_nhanh_code = cac_nhanh.some((n) => n.ma_nhom === "xu_ly_ky_thuat");
    if (co_nhanh_code || tong_do_dai_prompt > 180) {
        return "qwen2.5-coder:7b";
    }
    return "qwen2.5:3b";
}

export function tao_noi_dung_phan_hoi_da_nhanh(noi_dung_prompt, cac_nhanh, ten_model, thoi_gian_chot) {
    if (cac_nhanh.length <= 1) {
        const nhanh = cac_nhanh[0];
        return [
            `Đã xử lý xong bằng ${ten_model} (${thoi_gian_chot}) · Nhóm: ${nhanh ? nhanh.ten_nhom : "Tổng quát"}`,
            "",
            `- Yêu cầu: ${noi_dung_prompt}`,
            "- Trạng thái: Hoàn tất trên luồng cuộn chính, giữ nguyên mạch hiển thị mở.",
        ].join("\n");
    }

    const dong_cac_nhanh = cac_nhanh.map(
        (nhanh) => `- [Nhánh ${nhanh.so_nhanh} · ${nhanh.ten_nhom}] ${nhanh.noi_dung}`
    );

    return [
        `Đã tách và xử lý ${cac_nhanh.length} nhánh ý định bằng ${ten_model} trong ${thoi_gian_chot}:`,
        "",
        ...dong_cac_nhanh,
        "",
        "- Tổng hợp: Đã gom đầy đủ kết quả từng nhánh theo đúng thứ tự trong cùng một luồng phản hồi.",
    ].join("\n");
}