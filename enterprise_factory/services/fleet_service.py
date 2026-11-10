# File: enterprise_factory/services/fleet_service.py
from enterprise_factory.models import AgentDiscussion, AgentRegistry, Company

def process_fleet_dispatch_directive(directive, company_code='GLOBAL'):
    """
    Chuyên gia Logistics & DEV_BE phối hợp xử lý chỉ đạo điều xe
    """
    company = Company.objects.filter(code=company_code).first()
    logistics_agent = AgentRegistry.objects.filter(agent_id='EXPERT_LOGISTICS').first()
    dev_agent = AgentRegistry.objects.filter(agent_id='DEV_BE_01').first()

    # Step 1: Logistics Expert phân tích nghiệp vụ
    AgentDiscussion.objects.create(
        company=company,
        directive=directive,
        agent=logistics_agent or AgentRegistry.objects.first(),
        phase='ARCHITECTURE',
        message_content="[EXPERT_LOGISTICS]: Đã bóc tách nghiệp vụ Trợ lý Điều Xe:\n"
                        "1. Quản lý danh mục Xe (Biển số, Loại xe 4/7 chỗ, Trạng thái).\n"
                        "2. Quản lý Danh sách Tài xế & Số điện thoại liên hệ.\n"
                        "3. Tiếp nhận phiếu Đặt xe công tác từ Cán bộ -> Tự động kiểm tra trùng lịch -> Gán xe & Tài xế."
    )

    # Step 2: Dev BE đề xuất cấu trúc Data & API
    AgentDiscussion.objects.create(
        company=company,
        directive=directive,
        agent=dev_agent or AgentRegistry.objects.first(),
        phase='CODING',
        message_content="[DEV_BE_01]: Đã khởi tạo cấu trúc module `fleet_app/models.py` gồm 3 Table:\n"
                        "- `Vehicle` (id, license_plate, model, status)\n"
                        "- `Driver` (id, full_name, phone, is_available)\n"
                        "- `BookingRequest` (id, requester, destination, start_time, end_time, status)\n"
                        "Đã sẵn sàng sinh Vibercode qua Ollama!"
    )