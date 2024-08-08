import logging
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Set up logger
logger = logging.getLogger('UnifiedBot')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Expanded COLORS dictionary
COLORS = {
    'header': Fore.WHITE + Back.BLUE,
    'info': Fore.BLACK + Back.CYAN,
    'success': Fore.BLACK + Back.GREEN,
    'warning': Fore.BLACK + Back.YELLOW,
    'error': Fore.WHITE + Back.RED,
    'reset': Style.RESET_ALL
}

def print_header(message):
    print(f"{COLORS['header']}=== {message} ==={COLORS['reset']}")

def log_info(message):
    logger.info(f"{COLORS['info']}{message}{COLORS['reset']}")

def log_success(message):
    logger.info(f"{COLORS['success']}{message}{COLORS['reset']}")

def log_warning(message):
    logger.warning(f"{COLORS['warning']}{message}{COLORS['reset']}")

def log_error(message):
    logger.error(f"{COLORS['error']}{message}{COLORS['reset']}")