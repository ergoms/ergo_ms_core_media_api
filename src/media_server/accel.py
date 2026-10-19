"""Отдача файла через nginx после проверки подписи.

media_api больше не читает байты: заголовок X-Accel-Redirect указывает
внутренний location, а Range и sendfile делает nginx.
Прямой запрос на порт media_api при включённом флаге получит пустое тело —
публичный путь только через nginx.
"""

from __future__ import annotations

import os
from urllib.parse import quote

from django.http import HttpResponse, JsonResponse

MEDIA_ACCEL_PREFIX = '/_ergo_media/'


def accel_redirect_enabled() -> bool:
    raw = os.getenv('MEDIA_ACCEL_REDIRECT', '').strip().lower()
    if raw in ('1', 'true', 'yes', 'on'):
        return True
    if raw in ('0', 'false', 'no', 'off'):
        return False
    return os.getenv('ERGO_PROXY', '').strip().lower() == 'nginx'


def accel_redirect_response(file_path: str, *, attachment: bool, content_type: str):
    normalized = file_path.replace('\\', '/')
    parts = [part for part in normalized.split('/') if part]
    if not parts or normalized.startswith('/') or any(part in {'.', '..'} for part in parts):
        return JsonResponse({'error': 'Недопустимый путь'}, status=400)
    uri = MEDIA_ACCEL_PREFIX + '/'.join(quote(part) for part in parts)
    # Пустой ответ Django иначе уходит как text/html, и nginx сохраняет этот тип.
    response = HttpResponse(status=200, content_type=content_type or 'application/octet-stream')
    filename = os.path.basename(file_path).replace('"', '')
    disposition = 'attachment' if attachment else 'inline'
    response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
    response['X-Accel-Redirect'] = uri
    return response
