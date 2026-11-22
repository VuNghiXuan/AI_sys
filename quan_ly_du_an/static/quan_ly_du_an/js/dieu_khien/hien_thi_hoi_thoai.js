/* ============================================================================
- File Path: quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/hien_thi_hoi_thoai.js
- Chuc nang: Render danh sach prompt (thu gon/mo rong) va phan hoi mo khong box
-            kem bo render Markdown (bang, tieu de, bullet, inline code, dam)
-            va nut replay, like, dislike, heart, copy, thoi gian gui & phan hoi.
- File lien quan: quan_ly_lich_su_cuon.js, dong_ho_va_nhip_ollama.js
- ============================================================================ */

const MA_STYLE_HOI_THOAI = "style-hien-thi-hoi-thoai-md";

function dam_bao_style_markdown() {
    if (typeof document === "undefined") return;
    if (document.getElementById(MA_STYLE_HOI_THOAI)) return;

    const the_style = document.createElement("style");
    the_style.id = MA_STYLE_HOI_THOAI;
    the_style.textContent = `
        .van-ban-phan-hoi {
            line-height: 1.55;
            word-break: break-word;
        }
        .van-ban-phan-hoi .md-h3 {
            margin: 12px 0 6px;
            font-size: 1rem;
            font-weight: 700;
            color: var(--xanh-ngoc, #38bdf8);
        }
        .van-ban-phan-hoi .md-ul {
            margin: 4px 0 8px 18px;
            padding: 0;
        }
        .van-ban-phan-hoi .md-ul li {
            margin: 3px 0;
        }
        .van-ban-phan-hoi .md-code {
            padding: 1px 5px;
            border-radius: 4px;
            background: rgba(148, 163, 184, 0.16);
            font-family: Consolas, Monaco, monospace;
            font-size: 0.9em;
        }
        .van-ban-phan-hoi .md-table-wrap {
            width: 100%;
            overflow-x: auto;
            margin: 8px 0 12px;
            border-radius: 8px;
            border: 1px solid rgba(148, 163, 184, 0.25);
        }
        .van-ban-phan-hoi .md-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.92rem;
        }
        .van-ban-phan-hoi .md-table th,
        .van-ban-phan-hoi .md-table td {
            border: 1px solid rgba(148, 163, 184, 0.22);
            padding: 7px 10px;
            text-align: left;
            vertical-align: top;
        }
        .van-ban-phan-hoi .md-table th {
            background: rgba(56, 189, 248, 0.12);
            font-weight: 600;
        }
        .van-ban-phan-hoi .md-table tbody tr:nth-child(even) {
            background: rgba(148, 163, 184, 0.05);
        }
    `;
    document.head.appendChild(the_style);
}

function thoat_html(chuoi) {
    return String(chuoi ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function dinh_dang_noi_dung_dong(chuoi_tho) {
    let da_thoat = thoat_html(chuoi_tho);
    da_thoat = da_thoat.replace(/`([^`\n]+)`/g, '<code class="md-code">$1</code>');
    da_thoat = da_thoat.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
    return da_thoat;
}

function la_dong_bang_md(dong) {
    return /^\s*\|.*\|\s*$/.test(dong || "");
}

function la_dong_phan_cach_bang_md(dong) {
    return /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$/.test(dong || "");
}

function tach_cac_o_bang(dong) {
    return String(dong || "")
        .trim()
        .replace(/^\||\|$/g, "")
        .split("|")
        .map((o) => dinh_dang_noi_dung_dong(o.trim()));
}

function render_phan_hoi_markdown(van_ban) {
    const cac_dong = String(van_ban ?? "").replace(/\r\n/g, "\n").split("\n");
    const khoi_html = [];
    let i = 0;
    let dang_mo_list = false;

    const dong_list_neu_can = () => {
        if (dang_mo_list) {
            khoi_html.push("</ul>");
            dang_mo_list = false;
        }
    };

    while (i < cac_dong.length) {
        const dong = cac_dong[i];
        const dong_sach = dong.trim();

        if (
            la_dong_bang_md(dong) &&
            i + 1 < cac_dong.length &&
            la_dong_phan_cach_bang_md(cac_dong[i + 1])
        ) {
            dong_list_neu_can();
            const cot_tieu_de = tach_cac_o_bang(dong);
            i += 2;
            const cac_hang = [];
            while (i < cac_dong.length && la_dong_bang_md(cac_dong[i])) {
                cac_hang.push(tach_cac_o_bang(cac_dong[i]));
                i++;
            }

            const th_html = cot_tieu_de.map((t) => `<th>${t}</th>`).join("");
            const tr_html = cac_hang
                .map((hang) => `<tr>${hang.map((o) => `<td>${o}</td>`).join("")}</tr>`)
                .join("");

            khoi_html.push(
                `<div class="md-table-wrap"><table class="md-table"><thead><tr>${th_html}</tr></thead><tbody>${tr_html}</tbody></table></div>`
            );
            continue;
        }

        if (!dong_sach) {
            dong_list_neu_can();
            i++;
            continue;
        }

        const khop_h3 = dong_sach.match(/^###\s+(.+)$/);
        if (khop_h3) {
            dong_list_neu_can();
            khoi_html.push(`<h3 class="md-h3">${dinh_dang_noi_dung_dong(khop_h3[1])}</h3>`);
            i++;
            continue;
        }

        const khop_bullet = dong.match(/^\s*(?:[-*]|\d+\.)\s+(.+)$/);
        if (khop_bullet) {
            if (!dang_mo_list) {
                khoi_html.push('<ul class="md-ul">');
                dang_mo_list = true;
            }
            khoi_html.push(`<li>${dinh_dang_noi_dung_dong(khop_bullet[1])}</li>`);
            i++;
            continue;
        }

        dong_list_neu_can();
        khoi_html.push(`<p style="margin: 4px 0;">${dinh_dang_noi_dung_dong(dong_sach)}</p>`);
        i++;
    }

    dong_list_neu_can();
    return khoi_html.join("");
}

export function dinh_dang_giay(tong_giay) {
    const giay_nguyen = Math.max(0, Math.floor(tong_giay));
    const phut = String(Math.floor(giay_nguyen / 60)).padStart(2, "0");
    const giay = String(giay_nguyen % 60).padStart(2, "0");
    return `${phut}:${giay}s`;
}

export function tao_bo_hien_thi_hoi_thoai({
    vung_danh_sach,
    khi_bam_replay,
    khi_cap_nhat_tuong_tac,
}) {
    dam_bao_style_markdown();
    let cac_luot = [];

    function dat_danh_sach_luot(danh_sach_moi) {
        cac_luot = danh_sach_moi;
        ve_lai_toan_bo();
    }

    function them_luot_moi(luot_moi) {
        cac_luot.push(luot_moi);
        ve_lai_toan_bo();
    }

    function chen_lich_su_dau(cac_luot_cu) {
        cac_luot = [...cac_luot_cu, ...cac_luot];
        ve_lai_toan_bo();
    }

    function xoa_tat_ca_luot() {
        cac_luot = [];
        ve_lai_toan_bo();
    }

    function lay_luot_theo_id(ma_luot) {
        return cac_luot.find((item) => item.ma_luot === ma_luot) || null;
    }

    function cap_nhat_luot(ma_luot, du_lieu_cap_nhat) {
        const muc = lay_luot_theo_id(ma_luot);
        if (!muc) return;
        Object.assign(muc, du_lieu_cap_nhat);
        ve_lai_toan_bo();
    }

    function ve_lai_toan_bo() {
        if (!cac_luot.length) {
            vung_danh_sach.innerHTML =
                '<div style="color: var(--chu-mo); text-align: center; padding: 32px 0;">Chưa có lượt hội thoại nào trong vùng này.</div>';
            return;
        }

        vung_danh_sach.innerHTML = cac_luot
            .map((luot) => {
                const dang_chay = luot.trang_thai === "dang_chay";
                const thoi_gian_hien_thi = dang_chay
                    ? `Đang xử lý (${dinh_dang_giay(luot.so_giay_chay || 0)})`
                    : `Phản hồi trong ${luot.thoi_gian_phan_hoi || "00:00s"}`;

                const lop_trang_thai_tg = dang_chay
                    ? "nhan-thoi-gian-phan-hoi dang-chay"
                    : "nhan-thoi-gian-phan-hoi";

                const lop_thu_gon = luot.da_mo_rong_prompt ? "" : "thu-gon";
                const nhan_nut_mo_rong = luot.da_mo_rong_prompt ? "Thu gọn prompt" : "Xem đủ prompt";

                const lop_like = luot.tuong_tac?.like ? "nut-tuong-tac kich-hoat" : "nut-tuong-tac";
                const lop_dislike = luot.tuong_tac?.dislike ? "nut-tuong-tac kich-hoat" : "nut-tuong-tac";
                const lop_heart = luot.tuong_tac?.heart ? "nut-tuong-tac kich-hoat-tim" : "nut-tuong-tac";

                return `
          <article class="luot-hoi-thoai" data-ma-luot="${thoat_html(luot.ma_luot)}">
            <div class="hang-prompt">
              <div class="khoi-prompt">
                <div class="dong-moc-thoi-gian">
                  <span>Prompt · Gửi lúc ${thoat_html(luot.gio_gui)}</span>
                </div>
                <div class="noi-dung-prompt ${lop_thu_gon}">${thoat_html(luot.prompt)}</div>
                <button type="button" class="nut-thu-gon-prompt" data-hanh-dong="mo_rong_prompt">
                  ${nhan_nut_mo_rong}
                </button>
              </div>
            </div>

            <div class="khoi-phan-hoi-mo">
              <div class="dong-thong-tin-phan-hoi">
                <strong style="color: var(--xanh-ngoc);">AI_Sys_v2</strong>
                <span>·</span>
                <span>Model: <strong>${thoat_html(luot.ten_model || "qwen2.5-coder:7b")}</strong></span>
                <span>·</span>
                <span class="${lop_trang_thai_tg}">${thoat_html(thoi_gian_hien_thi)}</span>
              </div>

              <div class="van-ban-phan-hoi">${render_phan_hoi_markdown(luot.phan_hoi)}</div>

              <div class="thanh-nut-tuong-tac">
                <button type="button" class="nut-tuong-tac" data-hanh-dong="replay">↻ Replay</button>
                <button type="button" class="${lop_like}" data-hanh-dong="like">👍 Like</button>
                <button type="button" class="${lop_dislike}" data-hanh-dong="dislike">👎 Dislike</button>
                <button type="button" class="${lop_heart}" data-hanh-dong="heart">♥ Heart</button>
                <button type="button" class="nut-tuong-tac" data-hanh-dong="copy">📋 Copy</button>
              </div>
            </div>
          </article>
        `;
            })
            .join("");
    }

    vung_danh_sach.addEventListener("click", async (su_kien) => {
        const nut = su_kien.target.closest("button[data-hanh-dong]");
        if (!nut) return;

        const bai_viet = nut.closest(".luot-hoi-thoai");
        if (!bai_viet) return;

        const ma_luot = bai_viet.getAttribute("data-ma-luot");
        const muc = lay_luot_theo_id(ma_luot);
        if (!muc) return;

        const hanh_dong = nut.getAttribute("data-hanh-dong");

        if (hanh_dong === "mo_rong_prompt") {
            muc.da_mo_rong_prompt = !muc.da_mo_rong_prompt;
            ve_lai_toan_bo();
            return;
        }

        if (hanh_dong === "replay") {
            khi_bam_replay(muc.prompt);
            return;
        }

        if (hanh_dong === "copy") {
            try {
                await navigator.clipboard.writeText(muc.phan_hoi || "");
                const chu_cu = nut.textContent;
                nut.textContent = "✓ Đã copy";
                setTimeout(() => {
                    nut.textContent = chu_cu;
                }, 1200);
            } catch (_loi) {
                nut.textContent = "Không copy được";
            }
            return;
        }

        if (["like", "dislike", "heart"].includes(hanh_dong)) {
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
            ve_lai_toan_bo();
            khi_cap_nhat_tuong_tac(muc);
        }
    });

    return {
        dat_danh_sach_luot,
        them_luot_moi,
        chen_lich_su_dau,
        xoa_tat_ca_luot,
        lay_luot_theo_id,
        cap_nhat_luot,
        ve_lai_toan_bo,
    };
}