"""Centralized logging configuration for aFDO system."""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

class aFDOLogger:
    """Centralized logger for all aFDO agents and components."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the logger (only once)."""
        if not self._initialized:
            self.log_dir = Path(__file__).parent.parent / "logs"
            self.log_file = self.log_dir / "system.log"
            self._setup_logging()
            aFDOLogger._initialized = True

    def _setup_logging(self):
        """Configure logging with file and console handlers."""
        # Ensure log directory exists
        self.log_dir.mkdir(exist_ok=True)

        # Clear log file on initialization (restart)
        with open(self.log_file, 'w') as f:
            f.write(f"{'='*80}\n")
            f.write(f"aFDO System Log - Started at {datetime.now().isoformat()}\n")
            f.write(f"{'='*80}\n\n")

        # Create logger
        self.logger = logging.getLogger("aFDO")
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        self.logger.handlers.clear()

        # File handler - detailed logging
        file_handler = logging.FileHandler(self.log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)-8s] [%(agent)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Console handler - important messages only
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '[%(levelname)s] %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def _log(self, level: int, agent_name: str, message: str, **kwargs):
        """Internal logging method with agent context."""
        extra = {'agent': agent_name}
        self.logger.log(level, message, extra=extra, **kwargs)

    def debug(self, agent_name: str, message: str):
        """Log debug message."""
        self._log(logging.DEBUG, agent_name, message)

    def info(self, agent_name: str, message: str):
        """Log info message."""
        self._log(logging.INFO, agent_name, message)

    def warning(self, agent_name: str, message: str):
        """Log warning message."""
        self._log(logging.WARNING, agent_name, message)

    def error(self, agent_name: str, message: str):
        """Log error message."""
        self._log(logging.ERROR, agent_name, message)

    def critical(self, agent_name: str, message: str):
        """Log critical message."""
        self._log(logging.CRITICAL, agent_name, message)

    def operation_start(self, agent_name: str, operation: str, caller_pid: str, parameters: dict):
        """Log operation start with details."""
        param_summary = self._summarize_params(parameters)
        self.info(
            agent_name,
            f"🔵 START {operation} | Caller: {caller_pid} | Params: {param_summary}"
        )

    def operation_success(self, agent_name: str, operation: str, duration: float, result_summary: str = ""):
        """Log successful operation completion."""
        msg = f"✅ SUCCESS {operation} | Duration: {duration:.3f}s"
        if result_summary:
            msg += f" | Result: {result_summary}"
        self.info(agent_name, msg)

    def operation_error(self, agent_name: str, operation: str, error: str, duration: float = None):
        """Log operation error."""
        msg = f"❌ ERROR {operation} | Error: {error}"
        if duration:
            msg += f" | Duration: {duration:.3f}s"
        self.error(agent_name, msg)

    def agent_call(self, caller: str, target: str, operation: str, cost: float = None):
        """Log inter-agent communication."""
        msg = f"📤 CALL {caller} → {target}.{operation}"
        if cost is not None:
            msg += f" | Cost: ${cost:.4f}"
        self.info(caller, msg)

    def agent_response(self, agent_name: str, caller: str, success: bool, duration: float):
        """Log agent response."""
        status = "✅" if success else "❌"
        self.info(
            agent_name,
            f"{status} RESPONSE to {caller} | Duration: {duration:.3f}s"
        )

    def registration(self, agent_name: str, pid: str, port: int, operations: list):
        """Log agent registration."""
        ops = ", ".join(operations)
        self.info(
            agent_name,
            f"📝 REGISTERED | PID: {pid} | Port: {port} | Operations: {ops}"
        )

    def heartbeat(self, agent_name: str, status: str = "active"):
        """Log heartbeat event."""
        self.debug(agent_name, f"💓 HEARTBEAT | Status: {status}")

    def budget_transaction(self, agent_name: str, action: str, amount: float, remaining: float):
        """Log budget transaction."""
        self.debug(
            agent_name,
            f"💰 BUDGET {action} | Amount: ${amount:.4f} | Remaining: ${remaining:.4f}"
        )

    def queue_event(self, agent_name: str, event: str, details: str = ""):
        """Log queue management event."""
        msg = f"📊 QUEUE {event}"
        if details:
            msg += f" | {details}"
        self.debug(agent_name, msg)

    def reputation_update(self, agent_name: str, old_score: float, new_score: float, reason: str):
        """Log reputation change."""
        change = new_score - old_score
        sign = "+" if change >= 0 else ""
        self.info(
            agent_name,
            f"⭐ REPUTATION {old_score:.2f} → {new_score:.2f} ({sign}{change:.2f}) | {reason}"
        )

    def startup(self, agent_name: str, version: str = None, config: dict = None):
        """Log agent startup."""
        msg = f"🚀 STARTUP"
        if version:
            msg += f" | Version: {version}"
        if config:
            config_summary = ", ".join(f"{k}={v}" for k, v in config.items())
            msg += f" | Config: {config_summary}"
        self.info(agent_name, msg)

    def shutdown(self, agent_name: str, reason: str = "normal"):
        """Log agent shutdown."""
        self.info(agent_name, f"🛑 SHUTDOWN | Reason: {reason}")

    def _summarize_params(self, params: dict, max_length: int = 100) -> str:
        """Create short summary of parameters."""
        if not params:
            return "{}"

        summary_parts = []
        for key, value in params.items():
            if isinstance(value, str):
                if len(value) > 50:
                    value_str = f"{value[:50]}..."
                else:
                    value_str = value
            elif isinstance(value, (dict, list)):
                value_str = f"{type(value).__name__}[{len(value)}]"
            else:
                value_str = str(value)
            summary_parts.append(f"{key}={value_str}")

        summary = ", ".join(summary_parts)
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        return f"{{{summary}}}"


# Global logger instance
_logger = aFDOLogger()

def get_logger() -> aFDOLogger:
    """Get the global logger instance."""
    return _logger


# Convenience functions for direct import
def log_info(agent_name: str, message: str):
    """Log info message."""
    _logger.info(agent_name, message)

def log_error(agent_name: str, message: str):
    """Log error message."""
    _logger.error(agent_name, message)

def log_debug(agent_name: str, message: str):
    """Log debug message."""
    _logger.debug(agent_name, message)

def log_warning(agent_name: str, message: str):
    """Log warning message."""
    _logger.warning(agent_name, message)

def log_operation_start(agent_name: str, operation: str, caller_pid: str, parameters: dict):
    """Log operation start."""
    _logger.operation_start(agent_name, operation, caller_pid, parameters)

def log_operation_success(agent_name: str, operation: str, duration: float, result_summary: str = ""):
    """Log operation success."""
    _logger.operation_success(agent_name, operation, duration, result_summary)

def log_operation_error(agent_name: str, operation: str, error: str, duration: float = None):
    """Log operation error."""
    _logger.operation_error(agent_name, operation, error, duration)

def log_startup(agent_name: str, version: str = None, config: dict = None):
    """Log agent startup."""
    _logger.startup(agent_name, version, config)

def log_shutdown(agent_name: str, reason: str = "normal"):
    """Log agent shutdown."""
    _logger.shutdown(agent_name, reason)
