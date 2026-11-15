# enterprise_factory/views/patch_api.py
"""
API quản lý, duyệt (Approve) hoặc từ chối (Reject) các bản vá code (CodePatchProposal).
Tương ứng với module hiển thị Code Diff / Patch Review trên giao diện War Room.
"""

import logging
import os
import shutil
import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from enterprise_factory.models import CodePatchProposal

logger = logging.getLogger(__name__)

@csrf_exempt
def api_viber_approve_patch(request):
    """API duyệt bản vá: Tự động Backup file cũ trước khi ghi đè mã nguồn mới"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        patch_id = data.get('patch_id')
        
        patch = CodePatchProposal.objects.filter(id=patch_id).first()
        if not patch:
            return JsonResponse({'status': 'error', 'message': f'Không tìm thấy bản vá với ID: {patch_id}'}, status=404)
            
        if patch.status == 'APPROVED':
            return JsonResponse({'status': 'success', 'message': 'Bản vá này đã được duyệt trước đó rồi!'})

        target_file = patch.target_file
        code_content = patch.code_content
        
        file_path = target_file if os.path.isabs(target_file) else os.path.join(settings.BASE_DIR, target_file)
        
        # Cơ chế Auto-Backup an toàn
        backup_dir = os.path.join(settings.BASE_DIR, '.vnx_backups')
        os.makedirs(backup_dir, exist_ok=True)
        if os.path.exists(file_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{os.path.basename(target_file)}.{timestamp}.bak"
            shutil.copy2(file_path, os.path.join(backup_dir, backup_filename))

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code_content)
            
        patch.status = 'APPROVED'
        patch.save()
        
        logger.info(f"[+] [PATCH APPROVAL] Đã áp dụng thành công bản vá cho file: {target_file}")
        return JsonResponse({
            'status': 'success', 
            'message': f'Đã duyệt và áp dụng thành công bản vá vào file: {target_file} (Đã backup an toàn)'
        })
        
    except Exception as e:
        logger.error(f"[-] [PATCH APPROVE ERROR]: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_viber_reject_patch(request):
    """API từ chối / hủy bản vá code"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        patch_id = data.get('patch_id')

        if not patch_id:
            return JsonResponse({'status': 'error', 'message': 'Thiếu patch_id!'}, status=400)

        patch = CodePatchProposal.objects.filter(id=patch_id).first()
        if not patch:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy bản vá!'}, status=404)

        patch.status = 'REJECTED'
        patch.save()

        logger.info(f"[*] [PATCH REJECT] Đã từ chối bản vá ID #{patch_id}")
        return JsonResponse({
            'status': 'success',
            'message': f'Đã hủy bản vá ID #{patch_id} thành công!'
        })

    except Exception as e:
        logger.error(f"[-] [PATCH REJECT ERROR]: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)