# PROJECT_MAP (Tự động đồng bộ)

- **Thư mục gốc:** `AI_sys`
- **Tổng số file quét:** 114
- **Số file nhóm điều phối ý định:** 32
- **File vượt ngưỡng >300 dòng:** 2
- **Cập nhật lần cuối:** 2026-11-24 23:10:16

## Danh sách File, Liên kết & Số dòng

| File | Dòng | Trạng thái | Linked Files | Chức năng |
| --- | ---: | --- | --- | --- |
| `dieu_phoi_y_dinh/__init__.py` | 0 | ✅ Chuẩn | - | - |
| `dieu_phoi_y_dinh/admin.py` | 3 | ✅ Chuẩn | - | - |
| `dieu_phoi_y_dinh/apps.py` | 14 | ✅ Chuẩn | __init__.py, urls.py, views.py | Khai bao cau hinh Django cho app dieu_phoi_y_dinh. |
| `dieu_phoi_y_dinh/cau_hinh/cau_hinh_y_dinh.json` | 236 | ✅ Chuẩn | - | - |
| `dieu_phoi_y_dinh/dich_vu/__init__.py` | 0 | ✅ Chuẩn | - | - |
| `dieu_phoi_y_dinh/dich_vu/bo_nho_va_cache.py` | 181 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py, | Quan ly lich su hoi thoai (kem y_dinh tung luot), ten nguoi dung |
| `dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py` | 254 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/tach_va_loc_y_dinh.py, | Dieu phoi prompt don/da y dinh, gan ngu canh luot truoc, ket hop |
| `dieu_phoi_y_dinh/dich_vu/dinh_tuyen/__init__.py` | 0 | ✅ Chuẩn | - | - |
| `dieu_phoi_y_dinh/dich_vu/dinh_tuyen/bo_dang_ky_y_dinh.py` | 162 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/dinh_tuyen/bo_dinh_tuyen_ngu_nghia.py, | Nap cau hinh y dinh tu JSON, khop tu khoa/ngu nghia va thuc thi |
| `dieu_phoi_y_dinh/dich_vu/dinh_tuyen/bo_dinh_tuyen_ngu_nghia.py` | 200 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/dinh_tuyen/bo_dang_ky_y_dinh.py, | Tinh vector embedding qua Ollama, do tuong dong cosine voi cau mau |
| `dieu_phoi_y_dinh/dich_vu/dinh_tuyen/khoi_tao_y_dinh.py` | 19 | ✅ Chuẩn | - | - |
| `dieu_phoi_y_dinh/dich_vu/hoc_tang_cuong_qa.py` | 166 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py, | Ghi nhan phan hoi dung/sai/dinh chinh tu hoi thoai de tang/giam |
| `dieu_phoi_y_dinh/dich_vu/tach_va_loc_y_dinh.py` | 286 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/dinh_tuyen/khoi_tao_y_dinh.py, | Chuan hoa prompt, phan mien nhanh tang 1, tach da y dinh theo |
| `dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/do_ma_nguon_ast.py` | 269 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/truy_van_db_va_ast.py, | Ket hop ban do du an (PROJECT_MAP) va quet AST de tra loi chinh xac |
| `dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/ho_tro_llm_he_thong.py` | 408 | ⚠️ >300 dòng | dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py, | Xu ly goi Ollama (tach model nhanh/code), loc ky tu CJK, quet AST |
| `dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/tra_cuu_mang.py` | 254 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py, | Tra cuu web truc tiep cho moi may cai dat, uu tien AI_SYS_SEARCH_URL |
| `dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py` | 236 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/truy_van_db_va_ast.py, | Thuc thi y dinh theo che_do_xu_ly, chuan hoa loi go ngan, nho ten, |
| `dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/truy_van_db_va_ast.py` | 248 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py, | Sinh bang DB (so sanh theo app hoac liet ke/thong ke theo model), |
| `dieu_phoi_y_dinh/du_lieu/bo_nho_hoc_qa.json` | 2486 | ⚠️ >300 dòng | - | - |
| `dieu_phoi_y_dinh/models.py` | 29 | ✅ Chuẩn | bo_nao_cache_cosine.py, truy_van_du_lieu.py | Luu tru ben vung prompt nguoi dung, ket qua hien thi, nhanh dieu phoi |
| `dieu_phoi_y_dinh/tests/__init__.py` | 0 | ✅ Chuẩn | - | - |
| `dieu_phoi_y_dinh/tests/test_bien_the_va_chong_bat_nham.py` | 92 | ✅ Chuẩn | ../dich_vu/khoi_tao_y_dinh.py, ../cau_hinh/cau_hinh_y_dinh.json, | Thu nghiem nhieu bien the cau hoi va dam bao cac cau hoi thuong |
| `dieu_phoi_y_dinh/tests/test_bo_cau_hoi_y_dinh.py` | 185 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py, | Kiem tra y dinh, noi dung phan hoi, mach hoi thoai va toc do |
| `dieu_phoi_y_dinh/tests/test_cac_y_dinh_he_thong.py` | 152 | ✅ Chuẩn | ../dich_vu/khoi_tao_y_dinh.py, ../dich_vu/bo_dang_ky_y_dinh.py, | Kiem tra cau hinh JSON, khop nhanh va thuc thi cho tat ca 10 y dinh |
| `dieu_phoi_y_dinh/tests/test_cau_hoi_he_thong.py` | 175 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py, | Kiem thu dinh tuyen, toc do phan hoi va do chinh xac tra loi khi |
| `dieu_phoi_y_dinh/tests/test_da_y_dinh_va_cau_lat_leo.py` | 124 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py, | Kiem thu cac prompt go thieu dau/thieu chu ngu, cau hoi lat leo, |
| `dieu_phoi_y_dinh/tests/test_hoi_lo_mo_nguoi_that.py` | 153 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py, | Kiem thu kha nang dieu phoi, nho ngu canh va toc do khi nguoi dung |
| `dieu_phoi_y_dinh/tests/test_tong_hop_dieu_phoi.py` | 202 | ✅ Chuẩn | dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py, | Kiem thu toan dien cac ca thieu dau, mo ho, nho ten, da y dinh, |
| `dieu_phoi_y_dinh/tests.py` | 3 | ✅ Chuẩn | - | - |
| `dieu_phoi_y_dinh/tests_danh_gia_dieu_phoi.py` | 84 | ✅ Chuẩn | dieu_phoi_nhanh.py, cau_hinh_ollama.py, tach_da_y_dinh.py | Chay tap prompt mau qua luong dieu phoi that de do thoi gian, |
| `dieu_phoi_y_dinh/urls.py` | 14 | ✅ Chuẩn | views.py | Khai bao endpoint API cho app dieu_phoi_y_dinh. |
| `dieu_phoi_y_dinh/views.py` | 38 | ✅ Chuẩn | urls.py, dich_vu/dieu_phoi_nhanh.py | Nhan prompt tu client va tra ve ket qua dieu phoi y dinh da tang. |
| `he_thong/__init__.py` | 0 | ✅ Chuẩn | - | - |
| `he_thong/asgi.py` | 16 | ✅ Chuẩn | - | - |
| `he_thong/settings.py` | 129 | ✅ Chuẩn | - | - |
| `he_thong/urls.py` | 16 | ✅ Chuẩn | [quan_ly_du_an/giao_dien/urls_giao_dien.py] | - |
| `he_thong/wsgi.py` | 16 | ✅ Chuẩn | - | - |
| `lat_cat_da_tao/ho_so_2/hop_dong_du_lieu.py` | 19 | ✅ Chuẩn | [quan_ly_du_an/dich_vu_dieu_phoi.py] | - |
| `lat_cat_da_tao/ho_so_2/kiem_tra_ket_qua.py` | 19 | ✅ Chuẩn | [quan_ly_du_an/dich_vu_dieu_phoi.py] | - |
| `lat_cat_da_tao/ho_so_2/tests/test_m1_hop_dong_du_lieu.py` | 18 | ✅ Chuẩn | - | - |
| `lat_cat_da_tao/ho_so_2/tests/test_m2_xu_ly_chinh.py` | 18 | ✅ Chuẩn | - | - |
| `lat_cat_da_tao/ho_so_2/tests/test_m3_kiem_tra_ket_qua.py` | 41 | ✅ Chuẩn | - | - |
| `lat_cat_da_tao/ho_so_2/xu_ly_chinh.py` | 19 | ✅ Chuẩn | [quan_ly_du_an/dich_vu_dieu_phoi.py] | - |
| `lat_cat_da_tao/kiem_tra_ket_qua.py` | 19 | ✅ Chuẩn | [quan_ly_du_an/dich_vu_dieu_phoi.py] | - |
| `lat_cat_da_tao/lat_cat_da_tao/xu_ly_chinh.py` | 19 | ✅ Chuẩn | [quan_ly_du_an/dich_vu_dieu_phoi.py] | - |
| `lat_cat_da_tao/tests/test_m2_xu_ly_chinh.py` | 18 | ✅ Chuẩn | - | - |
| `lat_cat_da_tao/tests/test_m3_kiem_tra_ket_qua.py` | 18 | ✅ Chuẩn | - | - |
| `lat_cat_da_tao/xu_ly_chinh.py` | 19 | ✅ Chuẩn | [quan_ly_du_an/dich_vu_dieu_phoi.py] | - |
| `manage.py` | 22 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/__init__.py` | 0 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/admin.py` | 114 | ✅ Chuẩn | [quan_ly_du_an/models.py] | - |
| `quan_ly_du_an/api_dieu_phoi.py` | 66 | ✅ Chuẩn | quan_ly_du_an/dich_vu/cau_noi_dieu_phoi.py, quan_ly_du_an/urls.py | Cung cap endpoint GET lich su tu DB va POST chay luong y dinh. |
| `quan_ly_du_an/apps.py` | 40 | ✅ Chuẩn | quan_ly_du_an/dich_vu/cap_nhat_project_map.py, PROJECT_MAP.md | Tu dong kich hoat quet va dong bo PROJECT_MAP.md khi khoi dong |
| `quan_ly_du_an/dich_vu/__init__.py` | 6 | ✅ Chuẩn | cau_noi_dieu_phoi.py | Danh dau thu muc dich_vu la Python package. |
| `quan_ly_du_an/dich_vu/cap_nhat_project_map.py` | 202 | ✅ Chuẩn | PROJECT_MAP.md, PROJECT_MAP_COMPACT.md, manage.py | Quet header file, lien ket file va so dong ma nguon de xuat |
| `quan_ly_du_an/dich_vu/cau_noi_dieu_phoi.py` | 124 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/dich_vu_dieu_phoi.py` | 273 | ✅ Chuẩn | [quan_ly_du_an/models.py] | - |
| `quan_ly_du_an/giao_dien/__init__.py` | 0 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/giao_dien/urls_giao_dien.py` | 20 | ✅ Chuẩn | [quan_ly_du_an/giao_dien/views_dieu_khien.py] | - |
| `quan_ly_du_an/giao_dien/views_dieu_khien.py` | 157 | ✅ Chuẩn | [quan_ly_du_an/models.py, quan_ly_du_an/dich_vu_dieu_phoi.py, quan_ly_du_an/tu_dong_lam_ro.py, quan_ly_du_an/goi_y_dau_muc.py, quan_ly_du_an/thuc_thi_dau_muc.py] | - |
| `quan_ly_du_an/giao_dien/views_project_map.py` | 28 | ✅ Chuẩn | quan_ly_du_an/dich_vu/cap_nhat_project_map.py, PROJECT_MAP.md | Endpoint POST de nguoi dung bam nut cap nhat PROJECT_MAP.md ngay. |
| `quan_ly_du_an/giao_dien/views_telemetry.py` | 18 | ✅ Chuẩn | services_telemetry.py, urls.py | Tra ve du lieu CPU, RAM, GPU va model Ollama thuc te dang JSON. |
| `quan_ly_du_an/goi_y_dau_muc.py` | 149 | ✅ Chuẩn | [quan_ly_du_an/models.py, quan_ly_du_an/dich_vu_dieu_phoi.py] | - |
| `quan_ly_du_an/models.py` | 120 | ✅ Chuẩn | [he_thong/settings.py] | - |
| `quan_ly_du_an/phan_luong_y_dinh.py` | 114 | ✅ Chuẩn | [quan_ly_du_an/models.py, quan_ly_du_an/dich_vu_dieu_phoi.py] | - |
| `quan_ly_du_an/services_telemetry.py` | 175 | ✅ Chuẩn | views_telemetry.py, workbench_studio.js | Lay thong so CPU/RAM/GPU thuc te tren may va danh sach model Ollama. |
| `quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/cam_trang_con_va_nut.js` | 75 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/dieu_khoi_render_bang.js` | 158 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/dong_ho_va_nhip_ollama.js` | 181 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/hien_thi_hoi_thoai.js` | 166 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/nap_lich_su_tu_db.js` | 84 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/quan_ly_lich_su_cuon.js` | 74 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/xu_ly_da_y_dinh.js` | 75 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/static/quan_ly_du_an/js/khoi_tao_ung_dung.js` | 239 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/templates/quan_ly_du_an/thanh_phan/cot_phai_thong_so_ollama.html` | 61 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/templates/quan_ly_du_an/thanh_phan/cot_trai_danh_muc.html` | 32 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/templates/quan_ly_du_an/thanh_phan/o_nhap_prompt_duoi.html` | 25 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/templates/quan_ly_du_an/thanh_phan/thanh_dieu_huong_tren.html` | 17 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/templates/quan_ly_du_an/thanh_phan/vung_hoi_thoai_giua.html` | 21 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/templates/quan_ly_du_an/trang_dieu_khien.html` | 35 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/tests.py` | 3 | ✅ Chuẩn | - | - |
| `quan_ly_du_an/thuc_thi_dau_muc.py` | 260 | ✅ Chuẩn | [quan_ly_du_an/models.py, quan_ly_du_an/dich_vu_dieu_phoi.py] | - |
| `quan_ly_du_an/tu_dong_lam_ro.py` | 155 | ✅ Chuẩn | [quan_ly_du_an/models.py, quan_ly_du_an/dich_vu_dieu_phoi.py] | - |
| `quan_ly_du_an/views.py` | 3 | ✅ Chuẩn | - | - |
| `test_da_y_dinh_registry.py` | 55 | ✅ Chuẩn | bo_dieu_phoi_da_y_dinh.py, khoi_tao_y_dinh.py, chi_muc_ma_nguon.py | Kiem thu prompt don va prompt da y dinh (co y trong Registry va y |
| `test_registry_y_dinh.py` | 69 | ✅ Chuẩn | khoi_tao_y_dinh.py, bo_dang_ky_y_dinh.py, truy_van_du_lieu.py | Kiem tra nap cau hinh JSON, khop y dinh qua Registry, do thoi gian |
| `xuong_tao_app/__init__.py` | 0 | ✅ Chuẩn | - | - |
| `xuong_tao_app/admin.py` | 3 | ✅ Chuẩn | - | - |
| `xuong_tao_app/apps.py` | 6 | ✅ Chuẩn | - | - |
| `xuong_tao_app/dich_vu/chuyen_huong_tao_app/__init__.py` | 12 | ✅ Chuẩn | cho_xac_nhan_tao_app.py, dieu_phoi_xac_nhan.py | Xuat cac ham dieu phoi hoi xac nhan va chuyen tab xuong_tao_app. |
| `xuong_tao_app/dich_vu/chuyen_huong_tao_app/cho_xac_nhan_tao_app.py` | 105 | ✅ Chuẩn | dieu_phoi_xac_nhan.py, dieu_phoi_nhanh.py | Nhan dien yeu cau tao app/duong dan nguon o prompt chinh, luu tam |
| `xuong_tao_app/dich_vu/chuyen_huong_tao_app/dieu_phoi_xac_nhan.py` | 120 | ✅ Chuẩn | cho_xac_nhan_tao_app.py, ../../giao_dien/trang_xuong_tao_app.py | Xu ly luong hoi xac nhan khi go tao app o prompt chinh, luu san |
| `xuong_tao_app/dich_vu/dang_ky_tab_app/__init__.py` | 23 | ✅ Chuẩn | quan_ly_registry_tab.py, nap_app_vao_he_thong.py | Xuat ham quan ly registry tab app va quy trinh nap app da test on |
| `xuong_tao_app/dich_vu/dang_ky_tab_app/nap_app_vao_he_thong.py` | 99 | ✅ Chuẩn | quan_ly_registry_tab.py | Kiem tra thu muc test rieng, sao chep ma nguon sang khu vuc tich |
| `xuong_tao_app/dich_vu/dang_ky_tab_app/quan_ly_registry_tab.py` | 152 | ✅ Chuẩn | nap_app_vao_he_thong.py | Doc va ghi cau hinh tab app da dang ky (1 tab chinh + cac chuc nang |
| `xuong_tao_app/dich_vu/quet_thu_muc/__init__.py` | 12 | ✅ Chuẩn | doc_tep_an_toan.py, quet_thu_muc_nguon.py | Xuat ham quet thu muc nguon va doc noi dung tep phuc vu tao app. |
| `xuong_tao_app/dich_vu/quet_thu_muc/doc_tep_an_toan.py` | 148 | ✅ Chuẩn | quet_thu_muc_nguon.py | Kiem tra tep va doc noi dung van ban/du lieu co gioi han dung |
| `xuong_tao_app/dich_vu/quet_thu_muc/quet_thu_muc_nguon.py` | 131 | ✅ Chuẩn | doc_tep_an_toan.py, ../thiet_ke_va_task/ | Kiem tra duong dan thu muc nguon, duyet danh sach tep hop le co |
| `xuong_tao_app/dich_vu/sinh_ma_sandbox/__init__.py` | 16 | ✅ Chuẩn | kiem_tra_ma_sinh.py, thuc_thi_sinh_sandbox.py | Xuat ham sinh code theo task vao moi truong test tach biet va kiem |
| `xuong_tao_app/dich_vu/sinh_ma_sandbox/kiem_tra_ma_sinh.py` | 122 | ✅ Chuẩn | thuc_thi_sinh_sandbox.py | Boc code sach tu phan hoi model, dam bao header file va logger, kiem |
| `xuong_tao_app/dich_vu/sinh_ma_sandbox/thuc_thi_sinh_sandbox.py` | 140 | ✅ Chuẩn | kiem_tra_ma_sinh.py, ../thiet_ke_va_task/chia_task_nguyen_tu.py | Goi model code (qwen2.5-coder:7b) cho tung task nguyen tu, kiem tra |
| `xuong_tao_app/dich_vu/thiet_ke_va_task/__init__.py` | 16 | ✅ Chuẩn | tom_tat_va_thiet_ke.py, chia_task_nguyen_tu.py | Xuat ham lap ban thiet ke nghiep vu va chia task nguyen tu cho |
| `xuong_tao_app/dich_vu/thiet_ke_va_task/chia_task_nguyen_tu.py` | 104 | ✅ Chuẩn | tom_tat_va_thiet_ke.py, ../sinh_ma_sandbox/ | Chuyen ban thiet ke app va cac chuc nang con thanh cac task nho |
| `xuong_tao_app/dich_vu/thiet_ke_va_task/tom_tat_va_thiet_ke.py` | 160 | ✅ Chuẩn | ../quet_thu_muc/quet_thu_muc_nguon.py, chia_task_nguyen_tu.py | Tong hop noi dung tep da quet va prompt nguoi dung, goi model nhe |
| `xuong_tao_app/dich_vu/tu_sua_va_nang_cap/__init__.py` | 23 | ✅ Chuẩn | khoanh_vung_va_sao_luu.py, vong_lap_tu_sua.py | Xuat ham khoanh vung file, sao luu/hoan tac va sua/nang cap app |
| `xuong_tao_app/dich_vu/tu_sua_va_nang_cap/khoanh_vung_va_sao_luu.py` | 121 | ✅ Chuẩn | vong_lap_tu_sua.py | Phan loai y do (sua loi hay nang cap), chon dung cac tep trong thu |
| `xuong_tao_app/dich_vu/tu_sua_va_nang_cap/vong_lap_tu_sua.py` | 193 | ✅ Chuẩn | khoanh_vung_va_sao_luu.py, | Thuc thi sua loi hoac nang cap cac tep duoc khoanh vung dua tren |
| `xuong_tao_app/giao_dien/__init__.py` | 11 | ✅ Chuẩn | trang_chu_view.py, ngu_canh_view.py | Xuat view chinh va ham luu ngu canh chuyen tab cho xuong_tao_app. |
| `xuong_tao_app/giao_dien/api_xuong_tao_app.py` | 230 | ✅ Chuẩn | ../dich_vu/quet_thu_muc/quet_thu_muc_nguon.py, | Cung cap cac endpoint JSON cho tung buoc tren trang xuong_tao_app |
| `xuong_tao_app/giao_dien/trang_xuong_tao_app.py` | 80 | ✅ Chuẩn | ../urls.py, ../dich_vu/chuyen_huong_tao_app/cho_xac_nhan_tao_app.py, | Xu ly hien thi trang Xuong Tao App ke thua khung chinh cua |
| `xuong_tao_app/models.py` | 3 | ✅ Chuẩn | - | - |
| `xuong_tao_app/templates/xuong_tao_app/trang_chu_xuong_tao_app.html` | 143 | ✅ Chuẩn | - | - |
| `xuong_tao_app/tests.py` | 3 | ✅ Chuẩn | - | - |
| `xuong_tao_app/urls.py` | 29 | ✅ Chuẩn | giao_dien/trang_xuong_tao_app.py, giao_dien/api_xuong_tao_app.py | Khai bao route giao dien chinh va cac endpoint thao tac tung buoc |
