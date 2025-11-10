"""
Minimal progress logging for clean terminal output
"""
import sys
import time
from datetime import datetime

class ProgressLogger:
    """Clean, minimal progress logger"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.start_time = None
        self.current_step = None
        
    def start(self, title):
        """Start processing"""
        self.start_time = time.time()
        print("\n" + "━" * 60)
        print(f"Processing: {title}")
        print("━" * 60 + "\n")
    
    def step(self, message, end=False):
        """Show a processing step"""
        if end:
            # Complete the current step
            print(f" ✓", flush=True)
        else:
            # Start new step
            print(f"▸ {message}...", end='', flush=True)
            self.current_step = message
    
    def step_detail(self, detail):
        """Add detail to current step (only in verbose mode)"""
        if self.verbose:
            print(f"\n  {detail}", end='', flush=True)
    
    def step_complete(self, info=""):
        """Complete current step with optional info"""
        if info:
            print(f" ✓ ({info})")
        else:
            print(f" ✓")
    
    def warning(self, message):
        """Show warning (only in verbose mode)"""
        if self.verbose:
            print(f"\n⚠ {message}")
    
    def error(self, message):
        """Show error"""
        print(f"\n✗ {message}")
    
    def complete(self):
        """Show completion"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            
            print("\n" + "━" * 60)
            print(f"✅ Complete in {minutes}m {seconds}s")
            print("━" * 60 + "\n")
    
    def debug(self, message):
        """Debug output (only in verbose mode)"""
        if self.verbose:
            print(f"  [DEBUG] {message}")
    
    def info(self, message):
        """Info output (always shown but subtle)"""
        if self.verbose:
            print(f"  ℹ {message}")

# Global logger instance
_logger = None

def get_logger(verbose=False):
    """Get or create progress logger"""
    global _logger
    if _logger is None:
        _logger = ProgressLogger(verbose=verbose)
    return _logger

def reset_logger():
    """Reset global logger (useful for testing)"""
    global _logger
    _logger = None

