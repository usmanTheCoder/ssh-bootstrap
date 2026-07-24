import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging():
    # Define log file path
    log_dir = Path.home() / ".ssh-bootstrap-manager"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Prevent adding handlers multiple times if setup_logging is called twice
    if logger.handlers:
        return
        
    # File handler with rotation (5MB per file, max 3 files)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    
    # Standard format
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s", 
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Optional console handler for development debugging
    if os.environ.get("SSH_MANAGER_DEBUG"):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
        
    try:
        import sentry_sdk
        import subprocess
        from dotenv import load_dotenv
        
        # Load environment variables from .env file
        load_dotenv(Path(__file__).parent.parent / ".env")
        
        def get_git_revision():
            try:
                app_dir = Path(__file__).parent.parent
                rev = subprocess.check_output(
                    ['git', 'rev-parse', 'HEAD'], 
                    cwd=app_dir, text=True, stderr=subprocess.DEVNULL
                ).strip()
                return f"ssh-bootstrap@{rev}"
            except Exception:
                return "ssh-bootstrap@latest"
                
        is_debug = bool(os.environ.get("SSH_MANAGER_DEBUG"))
        dsn = os.environ.get("SENTRY_DSN")
        
        if dsn:
            sentry_sdk.init(
                dsn=dsn,
                release=get_git_revision(),
            environment="development" if is_debug else "production",
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
            )
            logger.info(f"Sentry SDK initialized successfully for release: {get_git_revision()}")
        else:
            logger.info("SENTRY_DSN not found in environment; crash reporting is disabled.")
    except ImportError:
        logger.warning("sentry_sdk not installed; crash reporting disabled.")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        
    logger.info("Application logging initialized.")
