"""
core/plugins/__init__.py

VendStack Plugin System — Auto-discovery registry for all integrations.
"""
import importlib
import pkgutil
import logging
from enum import StrEnum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class PluginType(StrEnum):
    MARKETPLACE = 'marketplace'
    CARRIER = 'carrier'
    AGGREGATOR = 'aggregator'
    TPL = '3pl'
    DROPSHIP = 'dropship'
    ACCOUNTING = 'accounting'
    PAYMENTS = 'payments'
    RETURNS = 'returns'
    REPRICER = 'repricer'
    BARCODE = 'barcode'
    CRM = 'crm'
    DATA = 'data'
    IPAAS = 'ipaas'
    EDI = 'edi'
    MRP = 'mrp'
    SHIPPING_TOOL = 'shipping_tool'
    SERVICES = 'services'

@dataclass
class HealthStatus:
    status: str  # 'ok', 'error', 'warning'
    message: str = ''
    last_check: Optional[str] = None

@dataclass
class PluginConfig:
    plugin_id: str
    name: str
    plugin_type: PluginType
    icon: str
    version: str
    description: str
    config_schema: dict  # JSON schema for credentials
    is_connected: bool = False
    last_sync: Optional[str] = None

class PluginRegistry:
    """Singleton registry of all available plugins."""
    
    _instance = None
    _plugins: Dict[str, Type['Plugin']] = {}
    _installed: Dict[str, dict] = {}  # plugin_id → config
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._discover_plugins()
        return cls._instance
    
    def _discover_plugins(self):
        """Auto-discover all plugins in core/plugins/ subdirectories."""
        import core.plugins
        pkg_path = core.plugins.__path__
        
        for importer, modname, ispkg in pkgutil.iter_modules(pkg_path):
            if modname in ('__init__', 'base'):
                continue
            try:
                mod = importlib.import_module(f'core.plugins.{modname}')
                logger.info(f'[PluginRegistry] Discovered plugin: {modname}')
            except Exception as e:
                logger.error(f'[PluginRegistry] Failed to load {modname}: {e}')
    
    @classmethod
    def register(cls, plugin_type: PluginType, plugin_id: str, name: str, 
                 icon: str = '📦', version: str = '1.0.0', description: str = ''):
        """Decorator to register a plugin class."""
        def decorator(plugin_cls):
            cls._plugins[plugin_id] = plugin_cls
            plugin_cls.type = plugin_type
            plugin_cls.id = plugin_id
            plugin_cls.name = name
            plugin_cls.icon = icon
            plugin_cls.version = version
            plugin_cls.description = description
            logger.info(f'[PluginRegistry] Registered: {plugin_id} ({plugin_type})')
            return plugin_cls
        return decorator
    
    @classmethod
    def get(cls, plugin_id: str) -> Optional[Type['Plugin']]:
        return cls._plugins.get(plugin_id)
    
    @classmethod
    def list_by_type(cls, plugin_type: PluginType) -> List[Type['Plugin']]:
        return [p for p in cls._plugins.values() if p.type == plugin_type]
    
    @classmethod
    def list_all(cls) -> List[Type['Plugin']]:
        return list(cls._plugins.values())
    
    @classmethod
    def install(cls, plugin_id: str, config: dict) -> bool:
        """Mark a plugin as installed with config."""
        cls._installed[plugin_id] = config
        logger.info(f'[PluginRegistry] Installed plugin: {plugin_id}')
        return True
    
    @classmethod
    def uninstall(cls, plugin_id: str) -> bool:
        """Remove a plugin installation."""
        cls._installed.pop(plugin_id, None)
        return True
    
    @classmethod
    def is_installed(cls, plugin_id: str) -> bool:
        return plugin_id in cls._installed
    
    @classmethod
    def get_installed_config(cls, plugin_id: str) -> Optional[dict]:
        return cls._installed.get(plugin_id)

# Convenience decorators
def register(plugin_type: PluginType, plugin_id: str, name: str, icon: str = '📦', version: str = '1.0.0'):
    return PluginRegistry.register(plugin_type, plugin_id, name, icon, version)

# Import base plugin class
from core.plugins.base import Plugin

__all__ = [
    'Plugin', 'PluginType', 'PluginRegistry', 'PluginConfig', 'HealthStatus',
    'register', 'get_plugin', 'list_plugins', 'list_plugins_by_type',
]

def get_plugin(plugin_id: str) -> Optional[Type['Plugin']]:
    return PluginRegistry.get(plugin_id)

def list_plugins() -> List[Type['Plugin']]:
    return PluginRegistry.list_all()

def list_plugins_by_type(plugin_type: PluginType) -> List[Type['Plugin']]:
    return PluginRegistry.list_by_type(plugin_type)
