"""Маршрут хранилища: обычный корень и зоны из media_zones.yaml.

Удалённая зона пишет только туда. Чтение, пока файла на той стороне нет,
берёт местный корень — так перенос не прячет уже лежащие страницы.
"""

from __future__ import annotations

import logging
from typing import BinaryIO

from core.shared.media_zone_http import zone_delete, zone_meta, zone_open, zone_save
from core.shared.media_zones import MediaZone, match_media_zone

from .base import BaseStorage
from .local import LocalFileStorage

logger = logging.getLogger('media_server.storage')


class RoutedStorage(BaseStorage):
    def __init__(self, local: LocalFileStorage, zones: tuple[MediaZone, ...]):
        self._local = local
        self._zones = zones
        self._local_zones: dict[str, LocalFileStorage] = {}

    def uses_accel(self, path: str) -> bool:
        """nginx X-Accel видит только обычный корень. Чужой диск и чужой сервер — нет."""
        zone = match_media_zone(path, self._zones)
        if zone is None:
            return True
        if zone.mode == 'local':
            return False
        exists, _size = zone_meta(zone.base_url, zone.key, path)
        return not exists

    def _zone_local(self, zone: MediaZone) -> LocalFileStorage:
        storage = self._local_zones.get(zone.prefix)
        if storage is None:
            storage = LocalFileStorage(zone.root, create=False)
            self._local_zones[zone.prefix] = storage
        return storage

    def _remote_exists(self, zone: MediaZone, path: str) -> bool:
        exists, _size = zone_meta(zone.base_url, zone.key, path)
        return exists

    def save(self, path: str, content: BinaryIO) -> str:
        zone = match_media_zone(path, self._zones)
        if zone is None:
            return self._local.save(path, content)
        if zone.mode == 'local':
            return self._zone_local(zone).save(path, content)
        saved = zone_save(zone.base_url, zone.key, path, content)
        logger.info('Файл зоны записан на %s: %s', zone.base_url, path)
        return saved

    def open(self, path: str) -> BinaryIO:
        zone = match_media_zone(path, self._zones)
        if zone is None:
            return self._local.open(path)
        if zone.mode == 'local':
            return self._zone_local(zone).open(path)
        if self._remote_exists(zone, path):
            return zone_open(zone.base_url, zone.key, path)
        return self._local.open(path)

    def delete(self, path: str) -> bool:
        zone = match_media_zone(path, self._zones)
        if zone is None:
            return self._local.delete(path)
        if zone.mode == 'local':
            return self._zone_local(zone).delete(path)
        remote_deleted = zone_delete(zone.base_url, zone.key, path)
        local_deleted = self._local.delete(path)
        return remote_deleted or local_deleted

    def exists(self, path: str) -> bool:
        zone = match_media_zone(path, self._zones)
        if zone is None:
            return self._local.exists(path)
        if zone.mode == 'local':
            return self._zone_local(zone).exists(path)
        if self._remote_exists(zone, path):
            return True
        return self._local.exists(path)

    def size(self, path: str) -> int:
        zone = match_media_zone(path, self._zones)
        if zone is None:
            return self._local.size(path)
        if zone.mode == 'local':
            return self._zone_local(zone).size(path)
        exists, remote_size = zone_meta(zone.base_url, zone.key, path)
        if exists:
            return remote_size
        return self._local.size(path)

    def full_path(self, path: str) -> str:
        zone = match_media_zone(path, self._zones)
        if zone is None:
            return self._local.full_path(path)
        if zone.mode == 'local':
            return self._zone_local(zone).full_path(path)
        exists, _size = zone_meta(zone.base_url, zone.key, path)
        if exists:
            return path
        return self._local.full_path(path)

    def is_available(self) -> bool:
        return self._local.is_available()
