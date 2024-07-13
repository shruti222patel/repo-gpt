import logging
import warnings

from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3
warnings.filterwarnings("ignore", category=InsecureRequestWarning)


import logging

VERBOSE_INFO = 15

logging.addLevelName(VERBOSE_INFO, "VERBOSE_INFO")


def verbose_info(self, message, *args, **kws):
    if self.isEnabledFor(VERBOSE_INFO):
        self._log(VERBOSE_INFO, message, args, **kws)


logging.Logger.verbose_info = verbose_info


def configure_logging(log_level=None):
    logging.basicConfig(format="%(message)s", level=log_level or logging.INFO)
