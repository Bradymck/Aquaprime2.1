import importlib
import os
from shared_utils import logger

class PluginManager:
    def __init__(self, plugin_dir='plugins'):
        self.plugin_dir = plugin_dir
        self.plugins = {}

    def load_plugins(self):
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                plugin_name = filename[:-3]
                try:
                    module = importlib.import_module(f'{self.plugin_dir}.{plugin_name}')
                    if hasattr(module, 'setup'):
                        self.plugins[plugin_name] = module.setup
                        logger.info(f"Loaded plugin: {plugin_name}")
                except Exception as e:
                    logger.error(f"Error loading plugin {plugin_name}: {e}")

    async def initialize_plugins(self, bot):
        for plugin_name, setup_func in self.plugins.items():
            try:
                await setup_func(bot)
                logger.info(f"Initialized plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Error initializing plugin {plugin_name}: {e}")