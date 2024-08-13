import os
import importlib
from shared_utils import logger

class PluginManager:
    def __init__(self):
        self.plugins = []

    def load_plugins(self):
        plugin_dir = 'plugins'
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)
        for filename in os.listdir(plugin_dir):
            if filename.endswith('.py'):
                module_name = filename[:-3]
                module = importlib.import_module(f'plugins.{module_name}')
                self.plugins.append(module)
                logger.info(f"Loaded plugin: {module_name}")

    async def initialize_plugins(self, bot):
        for plugin in self.plugins:
            if hasattr(plugin, 'setup'):
                await plugin.setup(bot)