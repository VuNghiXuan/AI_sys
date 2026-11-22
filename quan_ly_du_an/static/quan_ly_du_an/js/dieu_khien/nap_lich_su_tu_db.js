/* ============================================================================
 * File Path: quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/nap_lich_su_tu_db.js
 * Chuc nang: Tai lich su hoi thoai cu hon tu DB (LichSuDieuPhoi) khi keo len dinh
 *            khung cuon, co fallback an toan neu API chua san sang.
 * File lien quan: quan_ly_lich_su_cuon.js, hien_thi_hoi_thoai.js, khoi_tao_ung_dung.js
 * ============================================================================ */

function dinh_dang_gio_tu_iso(chuoi_thoi_gian) {
    if (!chuoi_thoi_gian) return "--:--";
    const tg = new Date(chuoi_thoi_gian);
    if (Number.isNaN(tg.getTime())) return "--:--";
    const gio = String(tg.getHours()).padStart(2, "0");
    const phut = String(tg.getMinutes()).padStart(2, "0");
    return `${gio}:${phut}`;
}

export function chuan_hoa_ban_ghi_lich_su(ban_ghi) {
    return {
        ma_luot: `db_${ban_ghi.id}`,
        id_db: ban_ghi.id,
        gio_gui: dinh_dang_gio_tu_iso(ban_ghi.thoi_gian_tao),
        thoi_gian_phan_hoi: ban_ghi.trung_cache ? "Cache nhanh" : "Đã lưu DB",
        trang_thai: "hoan_tat",
        ten_model: ban_ghi.ten_linh_vuc || "qwen2.5-coder:7b",
        da_mo_rong_prompt: false,
        prompt: ban_ghi.prompt || "",
        phan_hoi: ban_ghi.ket_qua_hien_thi || "(Chưa có nội dung phản hồi lưu trong DB)",
        tuong_tac: { like: false, dislike: false, heart: false },
    };
}

export function tao_bo_nap_lich_su_db({
    duong_dan_api = "/dieu-phoi/api/lich-su/",
    kich_thuoc_trang = 10,
    lich_su_du_phong = [],
}) {
    let id_nho_nhat_da_tai = null;
    const kho_du_phong = [...lich_su_du_phong];

    function dat_id_nho_nhat(cac_luot) {
        for (const luot of cac_luot) {
            if (typeof luot.id_db === "number") {
                if (id_nho_nhat_da_tai === null || luot.id_db < id_nho_nhat_da_tai) {
                    id_nho_nhat_da_tai = luot.id_db;
                }
            }
        }
    }

    async function tai_trang_lich_su_cu_hon() {
        const tham_so = new URLSearchParams({ limit: String(kich_thuoc_trang) });
        if (id_nho_nhat_da_tai !== null) {
            tham_so.set("before_id", String(id_nho_nhat_da_tai));
        }

        try {
            const phan_hoi = await fetch(`${duong_dan_api}?${tham_so.toString()}`, {
                headers: { Accept: "application/json" },
            });
            if (phan_hoi.ok) {
                const du_lieu = await phan_hoi.json();
                const ds_tho = Array.isArray(du_lieu.items) ? du_lieu.items : [];
                if (!ds_tho.length) return [];

                // DB sap xep -id (moi nhat truoc), dao lai de chen theo thu tu thoi gian cu -> moi hon
                const cac_luot_moi = ds_tho.map(chuan_hoa_ban_ghi_lich_su).reverse();
                dat_id_nho_nhat(cac_luot_moi);
                return cac_luot_moi;
            }
        } catch (_loi) {
            // Chua noi API hoac dang test offline thi dung du lieu du phong
        }

        if (!kho_du_phong.length) return [];
        const goi_lay = kho_du_phong.splice(0, kich_thuoc_trang);
        dat_id_nho_nhat(goi_lay);
        return goi_lay;
    }

    return {
        dat_id_nho_nhat,
        tai_trang_lich_su_cu_hon,
    };
}