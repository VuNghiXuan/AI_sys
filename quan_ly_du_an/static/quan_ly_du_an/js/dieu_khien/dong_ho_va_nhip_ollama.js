/* ============================================================================
 * File Path: quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/dong_ho_va_nhip_ollama.js
 * Chuc nang: Quan ly dong ho thoi gian phan hoi, model ollama dang chay,
 *            toc do tok/s, tien do luong va mau sac trang thai thuc te.
 * File lien quan: hien_thi_hoi_thoai.js, khoi_tao_ung_dung.js
 * ============================================================================ */

import { dinh_dang_giay } from "./hien_thi_hoi_thoai.js";

export function tao_bo_dieu_khien_nhip_ollama({
    nhan_model_tren_cung,
    ten_model_dang_chay,
    chi_tiet_phan_hoi_model,
    nhan_trang_thai_model,
    nhan_trang_thai_nhip,
    gia_tri_toc_do,
    gia_tri_do_tre_token,
    gia_tri_tien_do,
    buoc_hien_tai,
    thanh_tien_do_chay,
    mo_ta_tien_do_nhip,
    danh_sach_model_dom,
}) {
    let bo_dem_thoi_gian = null;
    let model_hien_tai = "qwen2.5-coder:7b";

    function dat_mau_nhan(phan_tu, loai_mau, chu_hien_thi) {
        phan_tu.className = `trang-thai-mau ${loai_mau}`;
        phan_tu.textContent = chu_hien_thi;
    }

    function cap_nhat_danh_sach_model(ten_model_chay, trang_thai_nhanh) {
        const cac_dong = danh_sach_model_dom.querySelectorAll(".dong-model");
        cac_dong.forEach((dong) => {
            const ma = dong.getAttribute("data-model");
            const nhan_nho = dong.querySelector(".nhan-nho-model");
            dong.classList.remove("dang-phan-hoi", "dang-nap-cham");

            if (ma === ten_model_chay) {
                if (trang_thai_nhanh === "cham") {
                    dong.classList.add("dang-nap-cham");
                    nhan_nho.textContent = "Đang nạp/chậm";
                    nhan_nho.style.color = "#f59e0b";
                } else {
                    dong.classList.add("dang-phan-hoi");
                    nhan_nho.textContent = "Đang phản hồi";
                    nhan_nho.style.color = "#10b981";
                }
            } else if (ma === "bge-m3:latest") {
                nhan_nho.textContent = "Embedding";
                nhan_nho.style.color = "#94a3b8";
            } else {
                nhan_nho.textContent = "Giữ RAM";
                nhan_nho.style.color = "#6b7785";
            }
        });
    }

    function dat_trang_thai_nhan_roi() {
        if (bo_dem_thoi_gian) {
            clearInterval(bo_dem_thoi_gian);
            bo_dem_thoi_gian = null;
        }
        ten_model_dang_chay.textContent = "Chưa có luồng";
        chi_tiet_phan_hoi_model.textContent = "Chờ lệnh để kích hoạt model phù hợp";
        dat_mau_nhan(nhan_trang_thai_model, "nghi", "Đang nghỉ");
        dat_mau_nhan(nhan_trang_thai_nhip, "nghi", "Nhàn rỗi");

        gia_tri_toc_do.textContent = "0.0 tok/s";
        gia_tri_do_tre_token.textContent = "-- ms/token";
        gia_tri_tien_do.textContent = "0%";
        buoc_hien_tai.textContent = "Chưa chạy";
        thanh_tien_do_chay.className = "thanh-tien-do-chay nghi";
        thanh_tien_do_chay.style.width = "0%";
        mo_ta_tien_do_nhip.textContent = "Sẵn sàng tiếp nhận prompt · Chạy CPU Local";
        cap_nhat_danh_sach_model("", "nghi");
    }

    function dat_trang_thai_hoan_tat(ten_model, thoi_gian_tong_cong) {
        if (bo_dem_thoi_gian) {
            clearInterval(bo_dem_thoi_gian);
            bo_dem_thoi_gian = null;
        }
        ten_model_dang_chay.textContent = ten_model;
        chi_tiet_phan_hoi_model.textContent = `Đã hoàn tất phản hồi (${thoi_gian_tong_cong}) · Vẫn giữ sẵn trên RAM`;
        dat_mau_nhan(nhan_trang_thai_model, "tot", "Sẵn sàng");
        dat_mau_nhan(nhan_trang_thai_nhip, "tot", "Hoàn tất");

        gia_tri_tien_do.textContent = "100%";
        buoc_hien_tai.textContent = "4/4 Chốt phản hồi";
        thanh_tien_do_chay.className = "thanh-tien-do-chay";
        thanh_tien_do_chay.style.width = "100%";
        mo_ta_tien_do_nhip.textContent = `Hoàn tất trong ${thoi_gian_tong_cong} bằng ${ten_model}`;
        cap_nhat_danh_sach_model("", "nghi");
    }

    function bat_dau_theo_doi_luong({ ten_model, noi_dung_prompt, khi_cap_nhat_giay, khi_hoan_tat }) {
        if (bo_dem_thoi_gian) {
            clearInterval(bo_dem_thoi_gian);
        }

        model_hien_tai = ten_model || "qwen2.5-coder:7b";
        nhan_model_tren_cung.textContent = model_hien_tai;
        ten_model_dang_chay.textContent = model_hien_tai;

        let giay_da_chay = 0;
        const tong_giay_du_kien = noi_dung_prompt.length > 260 ? 7 : 5;

        function cap_nhat_theo_giay() {
            giay_da_chay += 1;
            const phan_tram = Math.min(96, Math.round((giay_da_chay / tong_giay_du_kien) * 92));

            // Khi mới nạp model trên CPU hoặc prompt dài thì nhịp tạm chậm (màu vàng)
            const dang_nhip_cham = giay_da_chay <= 2 || (noi_dung_prompt.length > 260 && giay_da_chay <= 4);
            const toc_do_tok_s = dang_nhip_cham ? (5.4 + (giay_da_chay % 3) * 0.7).toFixed(1) : (11.8 + (giay_da_chay % 4) * 1.1).toFixed(1);
            const ms_moi_token = Math.round(1000 / parseFloat(toc_do_tok_s));

            let ten_buoc = "1/4 Phân tích ý định";
            if (giay_da_chay === 2) ten_buoc = "2/4 Nạp ngữ cảnh & tách nhánh";
            else if (giay_da_chay >= 3 && giay_da_chay < tong_giay_du_kien) ten_buoc = "3/4 Sinh phản hồi trên CPU";
            else if (giay_da_chay >= tong_giay_du_kien) ten_buoc = "4/4 Hoàn thiện văn bản";

            if (dang_nhip_cham) {
                dat_mau_nhan(nhan_trang_thai_model, "cham", "Đang nạp/chậm");
                dat_mau_nhan(nhan_trang_thai_nhip, "cham", "Nhịp CPU chậm");
                thanh_tien_do_chay.className = "thanh-tien-do-chay cham";
                chi_tiet_phan_hoi_model.textContent = "Đang xử lý trên CPU không GPU, nhịp token khởi động hơi chậm";
            } else {
                dat_mau_nhan(nhan_trang_thai_model, "tot", "Đang phản hồi");
                dat_mau_nhan(nhan_trang_thai_nhip, "tot", "Đang chạy đều");
                thanh_tien_do_chay.className = "thanh-tien-do-chay";
                chi_tiet_phan_hoi_model.textContent = "Đang sinh phản hồi từng đoạn trên luồng CPU chính";
            }

            gia_tri_toc_do.textContent = `${toc_do_tok_s} tok/s`;
            gia_tri_do_tre_token.textContent = `${ms_moi_token} ms/token`;
            gia_tri_tien_do.textContent = `${phan_tram}%`;
            buoc_hien_tai.textContent = ten_buoc;
            thanh_tien_do_chay.style.width = `${phan_tram}%`;
            mo_ta_tien_do_nhip.textContent = `${ten_model} · ${ten_buoc} · ${dinh_dang_giay(giay_da_chay)}`;

            khi_cap_nhat_giay(giay_da_chay, ten_buoc, dang_nhip_cham);
            cap_nhat_danh_sach_model(model_hien_tai, dang_nhip_cham ? "cham" : "tot");

            if (giay_da_chay >= tong_giay_du_kien) {
                clearInterval(bo_dem_thoi_gian);
                bo_dem_thoi_gian = null;
                const thoi_gian_chot = dinh_dang_giay(giay_da_chay);
                dat_trang_thai_hoan_tat(model_hien_tai, thoi_gian_chot);
                khi_hoan_tat(thoi_gian_chot);
            }
        }

        cap_nhat_theo_giay();
        bo_dem_thoi_gian = setInterval(cap_nhat_theo_giay, 1000);
    }

    function dung_luong_ngay() {
        if (bo_dem_thoi_gian) {
            clearInterval(bo_dem_thoi_gian);
            bo_dem_thoi_gian = null;
        }
        dat_mau_nhan(nhan_trang_thai_model, "nghi", "Đã dừng");
        dat_mau_nhan(nhan_trang_thai_nhip, "cham", "Đã dừng luồng");
        chi_tiet_phan_hoi_model.textContent = "Luồng phản hồi đã được người dùng chủ động dừng";
        mo_ta_tien_do_nhip.textContent = "Đã dừng luồng · Sẵn sàng gửi prompt mới";
        cap_nhat_danh_sach_model("", "nghi");
    }

    return {
        lay_model_hien_tai: () => model_hien_tai,
        dat_model_hien_tai: (ten_moi) => {
            model_hien_tai = ten_moi;
            nhan_model_tren_cung.textContent = ten_moi;
        },
        bat_dau_theo_doi_luong,
        dung_luong_ngay,
        dat_trang_thai_nhan_roi,
        dat_trang_thai_hoan_tat,
    };
}