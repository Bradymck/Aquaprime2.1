import logging
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Set up logger
logger = logging.getLogger('UnifiedBot')
logging.basicConfig(level=logging.WARNING,  # Change to WARNING to reduce log verbosity
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def print_header(message):
    print(f"{Fore.CYAN}=== {message} ==={Style.RESET_ALL}")

# Expanded COLORS dictionary
COLORS = {
    'header': Fore.WHITE + Back.BLUE,
    'info': Fore.BLACK + Back.CYAN,
    'success': Fore.BLACK + Back.GREEN,
    'warning': Fore.BLACK + Back.YELLOW,
    'error': Fore.WHITE + Back.RED,
    'reset': Style.RESET_ALL
}

def log_info(message):
    logger.info(f"{COLORS['info']}{message}{COLORS['reset']}")

def log_success(message):
    logger.info(f"{COLORS['success']}{message}{COLORS['reset']}")

def log_warning(message):
    logger.warning(f"{COLORS['warning']}{message}{COLORS['reset']}")

def log_error(message):
    logger.error(f"{COLORS['error']}{message}{COLORS['reset']}")

# Example usage
if __name__ == "__main__":
    print_header("Aqua Prime Bot Initialization")
    log_info("Bot is starting...")
    log_success("Successfully connected to the database.")
    log_warning("This is a warning message.")
    log_error("This is an error message.")