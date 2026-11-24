/* ==========================================
 * File Path: quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/hien_thi_hoi_thoai.js
 * Module: HienThiHoiThoai
 * Linked Files: dieu_khoi_render_bang.js, quan_ly_lich_su_cuon.js, dong_ho_va_nhip_ollama.js
 * Purpose: Render danh sach prompt (thu gon/mo rong) va phan hoi mo khong box
 *          kem nut replay, like, dislike, heart, copy, thoi gian gui & phan hoi.
 * ========================================================================== */

import {
    dam_bao_style_markdown,
    render_phan_hoi_markdown,
    thoat_html,
} from "./dieu_khoi_render_bang.js";

const TEN_LOG = "[HienThiHoiThoai]";

export function dinh_dang_giay(tong_giay) {
    const giay_nguyen = Math.max(0, Math.floor(Number(tong_giay) || 0));
    const phut = String(Math.floor(giay_nguyen / 60)).padStart(2, "0");
    const giay = String(giay_nguyen % 60).padStart(2, "0");
    return `${phut}:${giay}s`;
}

function lay_lop_nut_tuong_tac(luot, khoa) {
    if (!luot.tuong_tac || !luot.tuong_tac[khoa]) {
        return "nut-tuong-tac";
    }
    return khoa === "heart"
        ? "nut-tuong-tac kich-hoat-tim"
        : "nut-tuong-tac kich-hoat";
}

function render_mot_luot(luot) {
    const dang_chay = luot.trang_thai === "dang_chay";
    const thoi_gian_hien_thi = dang_chay
        ? `Đang xử lý (${dinh_dang_giay(luot.so_giay_chay || 0)})`
        : `Phản hồi trong ${luot.thoi_gian_phan_hoi || "00:00s"}`;
    const lop_trang_thai_tg = dang_chay
        ? "nhan-thoi-gian-phan-hoi dang-chay"
        : "nhan-thoi-gian-phan-hoi";
    const lop_thu_gon = luot.da_mo_rong_prompt ? "" : "thu-gon";
    const nhan_nut_mo_rong = luot.da_mo_rong_prompt ? "Thu gọn prompt" : "Xem đủ prompt";
    const noi_dung_html = render_phan_hoi_markdown(luot.phan_hoi);

    return `
      <article class="luot-hoi-thoai" data-ma-luot="${thoat_html(luot.ma_luot)}">
        <div class="hang-prompt">
          <div class="khoi-prompt">
            <div class="dong-moc-thoi-gian"><span>Prompt · Gửi lúc ${thoat_html(luot.gio_gui)}</span></div>
            <div class="noi-dung-prompt ${lop_thu_gon}">${thoat_html(luot.prompt)}</div>
            <button type="button" class="nut-thu-gon-prompt" data-hanh-dong="mo_rong_prompt">${nhan_nut_mo_rong}</button>
          </div>
        </div>
        <div class="khoi-phan-hoi-mo">
          <div class="dong-thong-tin-phan-hoi">
            <strong style="color: var(--xanh-ngoc);">AI_Sys</strong><span>·</span>
            <span>Model: <strong>${thoat_html(luot.ten_model || "qwen2.5-coder:7b")}</strong></span><span>·</span>
            <span class="${lop_trang_thai_tg}">${thoat_html(thoi_gian_hien_thi)}</span>
          </div>
          <div class="van-ban-phan-hoi">${noi_dung_html}</div>
          <div class="thanh-nut-tuong-tac">
            <button type="button" class="nut-tuong-tac" data-hanh-dong="replay">↻ Replay</button>
            <button type="button" class="${lay_lop_nut_tuong_tac(luot, "like")}" data-hanh-dong="like">👍 Like</button>
            <button type="button" class="${lay_lop_nut_tuong_tac(luot, "dislike")}" data-hanh-dong="dislike">👎 Dislike</button>
            <button type="button" class="${lay_lop_nut_tuong_tac(luot, "heart")}" data-hanh-dong="heart">♥ Heart</button>
            <button type="button" class="nut-tuong-tac" data-hanh-dong="copy">📋 Copy</button>
          </div>
        </div>
      </article>
    `;
}

function cap_nhat_trang_thai_tuong_tac(muc, hanh_dong) {
    muc.tuong_tac = muc.tuong_tac || { like: false, dislike: false, heart: false };
    if (hanh_dong === "like") {
        muc.tuong_tac.like = !muc.tuong_tac.like;
        if (muc.tuong_tac.like) muc.tuong_tac.dislike = false;
    } else if (hanh_dong === "dislike") {
        muc.tuong_tac.dislike = !muc.tuong_tac.dislike;
        if (muc.tuong_tac.dislike) muc.tuong_tac.like = false;
    } else if (hanh_dong === "heart") {
        muc.tuong_tac.heart = !muc.tuong_tac.heart;
    }
}

async function sao_chep_van_ban(nut, noi_dung) {
    try {
        await navigator.clipboard.writeText(noi_dung || "");
        const chu_cu = nut.textContent;
        nut.textContent = "✓ Đã copy";
        setTimeout(() => { nut.textContent = chu_cu; }, 1200);
    } catch (loi) {
        console.warn(`${TEN_LOG} Khong copy duoc vao clipboard:`, loi);
        nut.textContent = "Không copy được";
    }
}

export function tao_bo_hien_thi_hoi_thoai({ vung_danh_sach, khi_bam_replay, khi_cap_nhat_tuong_tac }) {
    if (!vung_danh_sach) {
        console.error(`${TEN_LOG} Thieu vung_danh_sach DOM de render hoi thoai.`);
    }
    dam_bao_style_markdown();
    let cac_luot = [];

    const ve_lai_toan_bo = () => {
        if (!vung_danh_sach) return;
        if (!cac_luot.length) {
            vung_danh_sach.innerHTML = '<div style="color: var(--chu-mo); text-align: center; padding: 32px 0;">Chưa có lượt hội thoại nào trong vùng này.</div>';
            return;
        }
        vung_danh_sach.innerHTML = cac_luot.map(render_mot_luot).join("");
    };

    const lay_luot_theo_id = (ma_luot) => cac_luot.find((item) => item.ma_luot === ma_luot) || null;

    vung_danh_sach?.addEventListener("click", async (su_kien) => {
        const nut = su_kien.target.closest("button[data-hanh-dong]");
        if (!nut) return;
        const bai_viet = nut.closest(".luot-hoi-thoai");
        const muc = bai_viet ? lay_luot_theo_id(bai_viet.getAttribute("data-ma-luot")) : null;
        if (!muc) return;

        const hanh_dong = nut.getAttribute("data-hanh-dong");
        if (hanh_dong === "mo_rong_prompt") {
            muc.da_mo_rong_prompt = !muc.da_mo_rong_prompt;
            ve_lai_toan_bo();
        } else if (hanh_dong === "replay") {
            khi_bam_replay?.(muc.prompt);
        } else if (hanh_dong === "copy") {
            await sao_chep_van_ban(nut, muc.phan_hoi);
        } else if (["like", "dislike", "heart"].includes(hanh_dong)) {
            cap_nhat_trang_thai_tuong_tac(muc, hanh_dong);
            ve_lai_toan_bo();
            khi_cap_nhat_tuong_tac?.(muc);
        }
    });

    return {
        dat_danh_sach_luot: (ds) => {
            cac_luot = Array.isArray(ds) ? ds : [];
            ve_lai_toan_bo();
        },
        them_luot_moi: (luot) => {
            if (!luot) return;
            cac_luot.push(luot);
            ve_lai_toan_bo();
        },
        chen_lich_su_dau: (cu) => {
            cac_luot = [...(Array.isArray(cu) ? cu : []), ...cac_luot];
            ve_lai_toan_bo();
        },
        xoa_tat_ca_luot: () => {
            cac_luot = [];
            ve_lai_toan_bo();
        },
        lay_luot_theo_id,
        cap_nhat_luot: (ma, patch) => {
            const m = lay_luot_theo_id(ma);
            if (m && patch && typeof patch === "object") {
                Object.assign(m, patch);
                ve_lai_toan_bo();
            }
        },
        ve_lai_toan_bo,
    };
}