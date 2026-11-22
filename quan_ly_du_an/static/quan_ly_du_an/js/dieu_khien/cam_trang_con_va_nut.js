/* ============================================================================
 * File Path: quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/cam_trang_con_va_nut.js
 * Chuc nang: Xu ly them trang con / module JS vao cot trai, nut dung luong,
 *            nut xoa vung va chuyen doi trang/che do.
 * File lien quan: khoi_tao_ung_dung.js
 * ============================================================================ */

export function tao_bo_dieu_khien_trang_va_nut({
    form_cam_trang_con,
    o_ten_trang_con,
    o_ten_module_js,
    danh_sach_trang_con,
    nut_dung_luong,
    nut_xoa_vung,
    nut_che_do_chinh,
    nut_che_do_tu_van,
    khi_dung_luong,
    khi_xoa_vung,
    khi_doi_che_do,
}) {
    const cac_module_da_cam = [];

    function chon_nut_danh_muc(nut_duoc_chon) {
        document.querySelectorAll(".nut-danh-muc").forEach((nut) => {
            nut.classList.remove("dang-chon");
        });
        nut_duoc_chon.classList.add("dang-chon");
    }

    document.addEventListener("click", (su_kien) => {
        const nut_trang = su_kien.target.closest(".nut-danh-muc");
        if (!nut_trang) return;
        chon_nut_danh_muc(nut_trang);
    });

    form_cam_trang_con.addEventListener("submit", (su_kien) => {
        su_kien.preventDefault();
        const ten_trang = o_ten_trang_con.value.trim();
        const ten_js = o_ten_module_js.value.trim();
        if (!ten_trang) return;

        const nut_moi = document.createElement("button");
        nut_moi.type = "button";
        nut_moi.className = "nut-danh-muc";
        nut_moi.setAttribute("data-trang", ten_trang);
        nut_moi.setAttribute("data-module-js", ten_js || "tuy_chinh.js");
        nut_moi.innerHTML = `<span>${ten_trang}</span><span>MỚI</span>`;

        danh_sach_trang_con.appendChild(nut_moi);
        chon_nut_danh_muc(nut_moi);

        cac_module_da_cam.push({ ten_trang, ten_js: ten_js || "tuy_chinh.js" });
        o_ten_trang_con.value = "";
        o_ten_module_js.value = "";
    });

    nut_dung_luong.addEventListener("click", khi_dung_luong);
    nut_xoa_vung.addEventListener("click", khi_xoa_vung);

    nut_che_do_chinh.addEventListener("click", () => {
        nut_che_do_chinh.classList.add("dang-chon");
        nut_che_do_tu_van.classList.remove("dang-chon");
        khi_doi_che_do("luong_chinh");
    });

    nut_che_do_tu_van.addEventListener("click", () => {
        nut_che_do_tu_van.classList.add("dang-chon");
        nut_che_do_chinh.classList.remove("dang-chon");
        khi_doi_che_do("tu_van_chot_luong");
    });

    return {
        lay_danh_sach_module_da_cam: () => [...cac_module_da_cam],
    };
}