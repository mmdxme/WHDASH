"""Base Service Class - Parent for all service layer classes."""
import logging
from functools import wraps
from flask import session
from database import get_db, get_db_context


class BaseService:
    """Base class for all service layer classes providing common utilities."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_db(self):
        return get_db()

    def get_db_context(self):
        return get_db_context()

    @staticmethod
    def log_audit(entity_type, entity_id, action, user_id=None, **kwargs):
        from database import log_audit
        log_audit(entity_type, entity_id, action, user_id=user_id, **kwargs)

    def log_error(self, message, **kwargs):
        self.logger.error(f"{message} | {kwargs}")

    def log_info(self, message, **kwargs):
        self.logger.info(f"{message} | {kwargs}")

    def log_warning(self, message, **kwargs):
        self.logger.warning(f"{message} | {kwargs}")