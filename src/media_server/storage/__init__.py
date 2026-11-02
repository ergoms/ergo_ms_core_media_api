import logging

from django.conf import settings

from core.shared.media_zones import load_media_zones

from .local import LocalFileStorage
from .routed import RoutedStorage

logger = logging.getLogger('media_server.storage')

_storage_instance = None


def get_storage():
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    storage_type = getattr(settings, 'MEDIA_STORAGE_TYPE', 'local')

    if storage_type != 'local':
        raise ValueError(f"Неизвестный тип хранилища: {storage_type}")

    local = LocalFileStorage(root_path=getattr(settings, 'MEDIA_STORAGE_PATH', 'media'))
    zones = load_media_zones()
    if zones:
        logger.info('Зоны media: %s', ', '.join(zone.prefix for zone in zones))
        _storage_instance = RoutedStorage(local, zones)
    else:
        _storage_instance = local

    return _storage_instance


def reset_storage():
    global _storage_instance
    _storage_instance = None
