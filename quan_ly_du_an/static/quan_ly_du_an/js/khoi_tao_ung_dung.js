/* ============================================================================
- File Path: quan_ly_du_an/static/quan_ly_du_an/js/khoi_tao_ung_dung.js
- Chuc nang: Khoi tao ung dung AI_Sys, goi API xu ly y dinh & tai lich su DB,
-            dong bo dong ho, nhip ollama va thao tac nut tren khung cuon don.
- File lien quan: quan_ly_lich_su_cuon.js, hien_thi_hoi_thoai.js,
-                 dong_ho_va_nhip_ollama.js, cam_trang_con_va_nut.js,
-                 nap_lich_su_tu_db.js, xu_ly_da_y_dinh.js
- ============================================================================ */

import { tao_bo_dieu_khien_cuon } from "./dieu_khien/quan_ly_lich_su_cuon.js";
import { tao_bo_hien_thi_hoi_thoai } from "./dieu_khien/hien_thi_hoi_thoai.js";
import { tao_bo_dieu_khien_nhip_ollama } from "./dieu_khien/dong_ho_va_nhip_ollama.js";
import { tao_bo_dieu_khien_trang_va_nut } from "./dieu_khien/cam_trang_con_va_nut.js";
import { tao_bo_nap_lich_su_db } from "./dieu_khien/nap_lich_su_tu_db.js";
import "./dieu_khien/xu_ly_da_y_dinh.js";

function lay_gio_hien_tai() {
    const bay_gio = new Date();
    const gio = String(bay_gio.getHours()).padStart(2, "0");
    const phut = String(bay_gio.getMinutes()).padStart(2, "0");
    return `${gio}:${phut}`;
}

function lay_csrf_token() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") || "" : "";
}

function chuan_hoa_ket_qua_api(kq, noi_dung_goc, model_du_kien) {
    const du_lieu = kq && typeof kq === "object" ? kq : {};
    return {
        id_db: du_lieu.id_db ?? null,
        ten_model: du_lieu.ten_model || model_du_kien,
        thoi_gian_phan_hoi: du_lieu.thoi_gian_phan_hoi || "00:01s",
        phan_hoi: du_lieu.phan_hoi || `Đã xử lý yêu cầu: ${noi_dung_goc}`,
    };
}

document.addEventListener("DOMContentLoaded", async () => {
    const khung_cuon = document.getElementById("vungCuonHoiThoai");
    const nut_ve_cuoi = document.getElementById("nutVeCuoiTrang");
    const nhan_trang_thai_tai = document.getElementById("trangThaiTaiLichSu");
    const vung_danh_sach = document.getElementById("danhSachLuotHoiThoai");
    const o_nhap_prompt = document.getElementById("oNhapPrompt");
    const nut_gui_prompt = document.getElementById("nutGuiPrompt");

    const api_lich_su = document.body.getAttribute("data-api-lich-su") || "/quan-ly-du-an/api/lich-su/";
    const api_xu_ly_y_dinh = document.body.getAttribute("data-api-xu-ly-y-dinh") || "/quan-ly-du-an/api/xu-ly-y-dinh/";

    let ma_luot_dang_chay = null;
    let che_do_hien_tai = "luong_chinh";

    const bo_nap_lich_su = tao_bo_nap_lich_su_db({
        duong_dan_api: api_lich_su,
        kich_thuoc_trang: 8,
        lich_su_du_phong: [],
    });

    const bo_cuon = tao_bo_dieu_khien_cuon({
        khung_cuon,
        nut_ve_cuoi,
        nhan_trang_thai_tai,
        khi_tai_lich_su_cu: async () => {
            const cac_luot_cu = await bo_nap_lich_su.tai_trang_lich_su_cu_hon();
            if (!cac_luot_cu.length) return false;
            bo_hien_thi.chen_lich_su_dau(cac_luot_cu);
            return true;
        },
    });

    const bo_nhip = tao_bo_dieu_khien_nhip_ollama({
        nhan_model_tren_cung: document.getElementById("nhanModelTrenCung"),
        ten_model_dang_chay: document.getElementById("tenModelDangChay"),
        chi_tiet_phan_hoi_model: document.getElementById("chiTietPhanHoiModel"),
        nhan_trang_thai_model: document.getElementById("nhanTrangThaiModel"),
        nhan_trang_thai_nhip: document.getElementById("nhanTrangThaiNhip"),
        gia_tri_toc_do: document.getElementById("giaTriTocDo"),
        gia_tri_do_tre_token: document.getElementById("giaTriDoTreToken"),
        gia_tri_tien_do: document.getElementById("giaTriTienDo"),
        buoc_hien_tai: document.getElementById("buocHienTai"),
        thanh_tien_do_chay: document.getElementById("thanhTienDoChay"),
        mo_ta_tien_do_nhip: document.getElementById("moTaTienDoNhip"),
        danh_sach_model_dom: document.getElementById("danhSachModelOllama"),
    });

    const bo_hien_thi = tao_bo_hien_thi_hoi_thoai({
        vung_danh_sach,
        khi_bam_replay: (noi_dung_goc) => {
            gui_prompt_moi(noi_dung_goc);
        },
        khi_cap_nhat_tuong_tac: () => { },
    });

    tao_bo_dieu_khien_trang_va_nut({
        form_cam_trang_con: document.getElementById("formCamTrangCon"),
        o_ten_trang_con: document.getElementById("tenTrangConMoi"),
        o_ten_module_js: document.getElementById("tenModuleJsMoi"),
        danh_sach_trang_con: document.getElementById("danhSachTrangCon"),
        nut_dung_luong: document.getElementById("nutDungLuong"),
        nut_xoa_vung: document.getElementById("nutXoaVung"),
        nut_che_do_chinh: document.getElementById("nutCheDoChinh"),
        nut_che_do_tu_van: document.getElementById("nutCheDoTuVan"),
        khi_dung_luong: () => {
            bo_nhip.dung_luong_ngay();
            if (ma_luot_dang_chay) {
                bo_hien_thi.cap_nhat_luot(ma_luot_dang_chay, {
                    trang_thai: "hoan_tat",
                    thoi_gian_phan_hoi: "Đã dừng",
                });
                ma_luot_dang_chay = null;
            }
        },
        khi_xoa_vung: () => {
            bo_nhip.dat_trang_thai_nhan_roi();
            bo_hien_thi.xoa_tat_ca_luot();
            bo_cuon.dat_lai_trang_thai_lich_su();
            ma_luot_dang_chay = null;
        },
        khi_doi_che_do: (che_do_moi) => {
            che_do_hien_tai = che_do_moi;
            const nhan_che_do = document.getElementById("nhanCheDoCuon");
            if (nhan_che_do) {
                nhan_che_do.textContent =
                    che_do_moi === "tu_van_chot_luong"
                        ? "Tư vấn & Chốt luồng · Neo đáy"
                        : "Neo đáy · Kéo đỉnh tải lịch sử";
            }
        },
    });

    async function gui_prompt_moi(noi_dung_nhap) {
        const noi_dung = (noi_dung_nhap || "").trim();
        if (!noi_dung) return;

        const model_du_kien = noi_dung.length > 220 ? "qwen2.5-coder:7b" : "qwen2.5:3b";
        const ma_luot = `luot_${Date.now()}`;
        ma_luot_dang_chay = ma_luot;

        bo_hien_thi.them_luot_moi({
            ma_luot,
            gio_gui: lay_gio_hien_tai(),
            thoi_gian_phan_hoi: "00:00s",
            so_giay_chay: 0,
            trang_thai: "dang_chay",
            ten_model: model_du_kien,
            da_mo_rong_prompt: false,
            prompt: noi_dung,
            phan_hoi: "Đang gửi yêu cầu tới bộ điều phối ý định...",
            tuong_tac: { like: false, dislike: false, heart: false },
        });
        bo_cuon.cuon_xuong_day_ngay();

        let giay_cho = 0;
        const bo_dem_cho = setInterval(() => {
            giay_cho += 1;
            bo_hien_thi.cap_nhat_luot(ma_luot, { so_giay_chay: giay_cho });
        }, 1000);

        bo_nhip.bat_dau_theo_doi_luong({
            ten_model: model_du_kien,
            noi_dung_prompt: noi_dung,
            khi_cap_nhat_giay: (so_giay, ten_buoc) => {
                bo_hien_thi.cap_nhat_luot(ma_luot, {
                    so_giay_chay: so_giay,
                    phan_hoi: `[${ten_buoc}] Đang phân tích ý định và ngữ cảnh...`,
                });
                bo_cuon.neo_day_neu_dang_o_cuoi();
            },
            khi_hoan_tat: () => { },
        });

        try {
            const phan_hoi_http = await fetch(api_xu_ly_y_dinh, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": lay_csrf_token(),
                },
                body: JSON.stringify({ prompt: noi_dung, che_do: che_do_hien_tai }),
            });
            const du_lieu = await phan_hoi_http.json();
            clearInterval(bo_dem_cho);
            ma_luot_dang_chay = null;

            if (!phan_hoi_http.ok || !du_lieu.ok) {
                bo_nhip.dung_luong_ngay();
                bo_hien_thi.cap_nhat_luot(ma_luot, {
                    trang_thai: "hoan_tat",
                    thoi_gian_phan_hoi: "Lỗi xử lý",
                    phan_hoi: du_lieu.loi || "Không thể xử lý yêu cầu từ máy chủ.",
                });
                return;
            }

            const kq = chuan_hoa_ket_qua_api(du_lieu.ket_qua, noi_dung, model_du_kien);
            bo_nap_lich_su.dat_id_nho_nhat([{ id_db: kq.id_db }]);
            bo_nhip.dat_trang_thai_hoan_tat(kq.ten_model, kq.thoi_gian_phan_hoi);
            bo_hien_thi.cap_nhat_luot(ma_luot, {
                id_db: kq.id_db,
                trang_thai: "hoan_tat",
                ten_model: kq.ten_model,
                thoi_gian_phan_hoi: kq.thoi_gian_phan_hoi,
                phan_hoi: kq.phan_hoi,
            });
            bo_cuon.neo_day_neu_dang_o_cuoi();
        } catch (loi) {
            clearInterval(bo_dem_cho);
            ma_luot_dang_chay = null;
            bo_nhip.dung_luong_ngay();
            bo_hien_thi.cap_nhat_luot(ma_luot, {
                trang_thai: "hoan_tat",
                thoi_gian_phan_hoi: "Mất kết nối",
                phan_hoi: `Lỗi kết nối tới API điều phối: ${loi.message || loi}`,
            });
        }
    }

    nut_gui_prompt.addEventListener("click", () => {
        gui_prompt_moi(o_nhap_prompt.value);
        o_nhap_prompt.value = "";
        o_nhap_prompt.focus();
    });

    o_nhap_prompt.addEventListener("keydown", (su_kien) => {
        if (su_kien.key === "Enter" && !su_kien.shiftKey) {
            su_kien.preventDefault();
            gui_prompt_moi(o_nhap_prompt.value);
            o_nhap_prompt.value = "";
        }
    });

    // Nạp các lượt lịch sử mới nhất từ DB lúc mở trang và luôn neo đáy
    bo_nhip.dat_trang_thai_nhan_roi();
    const lich_su_ban_dau = await bo_nap_lich_su.tai_trang_lich_su_cu_hon();
    if (lich_su_ban_dau.length) {
        bo_hien_thi.dat_danh_sach_luot(lich_su_ban_dau);
    }
    bo_cuon.cuon_xuong_day_ngay();
});