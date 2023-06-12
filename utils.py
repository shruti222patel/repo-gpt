import logging
import warnings

from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# Create a logger
logger = logging.getLogger("repo_gpt")
logger.setLevel(logging.INFO)

# Create a console handler
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

# Create a formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Attach the formatter to the handler
handler.setFormatter(formatter)

# Attach the handler to the logger
logger.addHandler(handler)
