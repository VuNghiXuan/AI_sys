/* ============================================================================
- File Path: quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/dieu_khoi_render_bang.js
- Chuc nang: Style va bo chuyen doi Markdown (bang, tieu de H3, bullet, inline
-            code, chu dam) sang HTML an toan cho khu vuc hien thi hoi thoai.
- File lien quan: hien_thi_hoi_thoai.js
- ============================================================================ */

const MA_STYLE_HOI_THOAI = "style-hien-thi-hoi-thoai-md";

export function dam_bao_style_markdown() {
    if (typeof document === "undefined" || document.getElementById(MA_STYLE_HOI_THOAI)) return;

    const the_style = document.createElement("style");
    the_style.id = MA_STYLE_HOI_THOAI;
    the_style.textContent = `
        .van-ban-phan-hoi { line-height: 1.55; word-break: break-word; }
        .van-ban-phan-hoi .md-h3 {
            margin: 12px 0 6px; font-size: 1rem; font-weight: 700;
            color: var(--xanh-ngoc, #38bdf8);
        }
        .van-ban-phan-hoi .md-ul { margin: 4px 0 8px 18px; padding: 0; }
        .van-ban-phan-hoi .md-ul li { margin: 3px 0; }
        .van-ban-phan-hoi .md-code {
            padding: 1px 5px; border-radius: 4px;
            background: rgba(148, 163, 184, 0.16);
            font-family: Consolas, Monaco, monospace; font-size: 0.9em;
        }
        .van-ban-phan-hoi .md-table-wrap {
            width: 100%; overflow-x: auto; margin: 8px 0 12px;
            border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.25);
        }
        .van-ban-phan-hoi .md-table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
        .van-ban-phan-hoi .md-table th, .van-ban-phan-hoi .md-table td {
            border: 1px solid rgba(148, 163, 184, 0.22); padding: 7px 10px;
            text-align: left; vertical-align: top;
        }
        .van-ban-phan-hoi .md-table th {
            background: rgba(56, 189, 248, 0.12); font-weight: 600;
        }
        .van-ban-phan-hoi .md-table tbody tr:nth-child(even) {
            background: rgba(148, 163, 184, 0.05);
        }
    `;
    document.head.appendChild(the_style);
}

export function thoat_html(chuoi) {
    return String(chuoi ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function dinh_dang_noi_dung_dong(chuoi_tho) {
    return thoat_html(chuoi_tho)
        .replace(/`([^`\n]+)`/g, '<code class="md-code">$1</code>')
        .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
}

function la_dong_bang_md(dong) {
    const chuoi = String(dong || "").trim();
    if (!chuoi.includes("|")) return false;
    return /^\s*\|.*\|\s*$/.test(chuoi) || chuoi.split("|").filter(Boolean).length >= 2;
}

function la_dong_phan_cach_bang_md(dong) {
    return /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$/.test(String(dong || ""));
}

function tach_cac_o_bang(dong) {
    return String(dong || "")
        .trim()
        .replace(/^\||\|$/g, "")
        .split("|")
        .map((o) => dinh_dang_noi_dung_dong(o.trim()));
}

function render_khoi_bang_md(cac_dong, vi_tri_bat_dau) {
    const cot_tieu_de = tach_cac_o_bang(cac_dong[vi_tri_bat_dau]);
    let i = vi_tri_bat_dau + 2;
    const cac_hang = [];

    while (i < cac_dong.length && la_dong_bang_md(cac_dong[i])) {
        if (!la_dong_phan_cach_bang_md(cac_dong[i])) {
            cac_hang.push(tach_cac_o_bang(cac_dong[i]));
        }
        i++;
    }

    const th_html = cot_tieu_de.map((t) => `<th>${t}</th>`).join("");
    const tr_html = cac_hang
        .map((hang) => `<tr>${hang.map((o) => `<td>${o}</td>`).join("")}</tr>`)
        .join("");

    const html = `<div class="md-table-wrap"><table class="md-table"><thead><tr>${th_html}</tr></thead><tbody>${tr_html}</tbody></table></div>`;
    return { html, nextIndex: i };
}

export function render_phan_hoi_markdown(van_ban) {
    dam_bao_style_markdown();
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

        if (la_dong_bang_md(dong) && i + 1 < cac_dong.length && la_dong_phan_cach_bang_md(cac_dong[i + 1])) {
            dong_list_neu_can();
            const bang = render_khoi_bang_md(cac_dong, i);
            khoi_html.push(bang.html);
            i = bang.nextIndex;
            continue;
        }

        if (!dong_sach || la_dong_phan_cach_bang_md(dong_sach)) {
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