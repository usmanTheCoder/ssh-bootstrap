"""Entry point for the SSH Configuration Manager.

Supersedes remote_ssh_gui.py as the app's primary GUI. The old file is
left in place for now; its bootstrap logic (key gen, paramiko key upload)
has been refactored into sshmgr/keys.py and sshmgr/deploy.py and is used
from the new Add Server wizard's optional "deploy key now" step.
"""
from sshmgr.ui.app import run
from sshmgr.logging_config import setup_logging
import logging

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    setup_logging()
    logger.info("Starting SSH Configuration Manager")
    run()
