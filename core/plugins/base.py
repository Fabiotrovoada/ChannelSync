"""
core/plugins/base.py

Base classes for all VendStack plugins.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import StrEnum
from core.plugins import PluginType, HealthStatus

class Plugin(ABC):
    """Abstract base class for all VendStack plugins."""
    
    type: PluginType = None
    id: str = ''
    name: str = ''
    icon: str = '📦'
    version: str = '1.0.0'
    description: str = ''
    
    def __init__(self, config: dict):
        self.config = config
        self._health = HealthStatus(status='ok')
    
    # ── Lifecycle ──────────────────────────────────────────────────────────
    
    def install(self) -> bool:
        """Called when merchant installs the plugin."""
        logger.info(f'[{self.id}] Installing plugin')
        return True
    
    def uninstall(self) -> bool:
        """Called when merchant removes the plugin."""
        logger.info(f'[{self.id}] Uninstalling plugin')
        return True
    
    def health_check(self) -> HealthStatus:
        """Check plugin health (API connectivity, auth, etc)."""
        return HealthStatus(status='ok', last_check=datetime.utcnow().isoformat())
    
    def config_schema(self) -> dict:
        """Return JSON Schema for plugin config (credentials UI)."""
        return {
            'type': 'object',
            'properties': {},
            'required': [],
        }
    
    # ── Sync ─────────────────────────────────────────────────────────────
    
    def get_last_sync(self) -> Optional[str]:
        return getattr(self, '_last_sync', None)
    
    def set_last_sync(self, ts: str = None):
        self._last_sync = ts or datetime.utcnow().isoformat()
    
    def __repr__(self):
        return f'<Plugin {self.id} ({self.name})>'

import logging
logger = logging.getLogger(__name__)
