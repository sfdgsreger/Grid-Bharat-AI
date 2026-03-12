"""
Log rotation and management system for Bharat-Grid AI.

Provides automated log rotation, cleanup, and archival
to prevent disk space issues in production deployments.
"""

import os
import gzip
import shutil
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from monitoring import api_logger


class LogManager:
    """
    Automated log management with rotation and cleanup.
    
    Features:
    - Automatic log rotation by size and time
    - Compression of old log files
    - Cleanup of old archives
    - Monitoring of disk usage
    """
    
    def __init__(self, 
                 log_dir: str = "./logs",
                 max_file_size_mb: int = 100,
                 max_files_per_logger: int = 5,
                 archive_days: int = 30,
                 cleanup_interval_hours: int = 24):
        """
        Initialize log manager.
        
        Args:
            log_dir: Directory containing log files
            max_file_size_mb: Maximum size per log file in MB
            max_files_per_logger: Maximum number of files per logger
            archive_days: Days to keep archived logs
            cleanup_interval_hours: Hours between cleanup runs
        """
        self.log_dir = Path(log_dir)
        self.max_file_size_mb = max_file_size_mb
        self.max_files_per_logger = max_files_per_logger
        self.archive_days = archive_days
        self.cleanup_interval_hours = cleanup_interval_hours
        
        # Ensure log directory exists
        self.log_dir.mkdir(exist_ok=True)
        
        # Archive directory for compressed logs
        self.archive_dir = self.log_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
        
        # Cleanup thread
        self.cleanup_thread = None
        self.running = False
        
        api_logger.info(f"LogManager initialized: {log_dir}")
    
    def setup_rotating_handler(self, logger_name: str) -> RotatingFileHandler:
        """
        Set up rotating file handler for a logger.
        
        Args:
            logger_name: Name of the logger
            
        Returns:
            Configured rotating file handler
        """
        log_file = self.log_dir / f"{logger_name}.log"
        max_bytes = self.max_file_size_mb * 1024 * 1024  # Convert MB to bytes
        
        handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_bytes,
            backupCount=self.max_files_per_logger,
            encoding='utf-8'
        )
        
        # Set up JSON formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def setup_timed_handler(self, logger_name: str, when: str = 'midnight') -> TimedRotatingFileHandler:
        """
        Set up timed rotating file handler for a logger.
        
        Args:
            logger_name: Name of the logger
            when: When to rotate ('midnight', 'H', 'D', etc.)
            
        Returns:
            Configured timed rotating file handler
        """
        log_file = self.log_dir / f"{logger_name}_daily.log"
        
        handler = TimedRotatingFileHandler(
            filename=str(log_file),
            when=when,
            interval=1,
            backupCount=self.archive_days,
            encoding='utf-8'
        )
        
        # Set up formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def compress_log_file(self, file_path: Path) -> Optional[Path]:
        """
        Compress a log file using gzip.
        
        Args:
            file_path: Path to the log file to compress
            
        Returns:
            Path to compressed file or None if failed
        """
        try:
            compressed_path = self.archive_dir / f"{file_path.name}.gz"
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file after successful compression
            file_path.unlink()
            
            api_logger.info(f"Compressed log file: {file_path} -> {compressed_path}")
            return compressed_path
            
        except Exception as e:
            api_logger.error(f"Failed to compress log file {file_path}: {e}")
            return None
    
    def cleanup_old_logs(self):
        """Clean up old log files and archives"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.archive_days)
            cleaned_count = 0
            
            # Clean up old rotated log files
            for log_file in self.log_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    # Compress before deletion if not already compressed
                    if not log_file.name.endswith('.gz'):
                        compressed = self.compress_log_file(log_file)
                        if compressed:
                            cleaned_count += 1
                    else:
                        log_file.unlink()
                        cleaned_count += 1
            
            # Clean up old archived files
            for archive_file in self.archive_dir.glob("*.gz"):
                if archive_file.stat().st_mtime < cutoff_date.timestamp():
                    archive_file.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                api_logger.info(f"Cleaned up {cleaned_count} old log files")
            
        except Exception as e:
            api_logger.error(f"Failed to cleanup old logs: {e}")
    
    def get_log_statistics(self) -> Dict[str, any]:
        """Get statistics about log files and disk usage"""
        try:
            stats = {
                'log_directory': str(self.log_dir),
                'archive_directory': str(self.archive_dir),
                'active_logs': [],
                'archived_logs': [],
                'total_size_mb': 0,
                'oldest_log': None,
                'newest_log': None
            }
            
            # Analyze active log files
            for log_file in self.log_dir.glob("*.log*"):
                if log_file.is_file():
                    file_stats = log_file.stat()
                    file_info = {
                        'name': log_file.name,
                        'size_mb': file_stats.st_size / (1024 * 1024),
                        'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                        'age_hours': (time.time() - file_stats.st_mtime) / 3600
                    }
                    stats['active_logs'].append(file_info)
                    stats['total_size_mb'] += file_info['size_mb']
            
            # Analyze archived log files
            for archive_file in self.archive_dir.glob("*.gz"):
                if archive_file.is_file():
                    file_stats = archive_file.stat()
                    file_info = {
                        'name': archive_file.name,
                        'size_mb': file_stats.st_size / (1024 * 1024),
                        'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                        'age_days': (time.time() - file_stats.st_mtime) / (24 * 3600)
                    }
                    stats['archived_logs'].append(file_info)
                    stats['total_size_mb'] += file_info['size_mb']
            
            # Find oldest and newest logs
            all_logs = stats['active_logs'] + stats['archived_logs']
            if all_logs:
                oldest = min(all_logs, key=lambda x: x['modified'])
                newest = max(all_logs, key=lambda x: x['modified'])
                stats['oldest_log'] = oldest
                stats['newest_log'] = newest
            
            return stats
            
        except Exception as e:
            api_logger.error(f"Failed to get log statistics: {e}")
            return {'error': str(e)}
    
    def start_cleanup_scheduler(self):
        """Start the automated cleanup scheduler"""
        if self.running:
            return
        
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        api_logger.info(f"Started log cleanup scheduler (interval: {self.cleanup_interval_hours}h)")
    
    def stop_cleanup_scheduler(self):
        """Stop the automated cleanup scheduler"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        
        api_logger.info("Stopped log cleanup scheduler")
    
    def _cleanup_loop(self):
        """Background cleanup loop"""
        while self.running:
            try:
                self.cleanup_old_logs()
                
                # Sleep for cleanup interval
                sleep_time = self.cleanup_interval_hours * 3600
                for _ in range(int(sleep_time)):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                api_logger.error(f"Error in cleanup loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def force_rotation(self, logger_name: str):
        """Force rotation of a specific logger's files"""
        try:
            log_file = self.log_dir / f"{logger_name}.log"
            if log_file.exists():
                # Create backup with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.log_dir / f"{logger_name}.log.{timestamp}"
                shutil.move(str(log_file), str(backup_file))
                
                # Compress the backup
                self.compress_log_file(backup_file)
                
                api_logger.info(f"Forced rotation for logger: {logger_name}")
                
        except Exception as e:
            api_logger.error(f"Failed to force rotation for {logger_name}: {e}")


# Global log manager instance
log_manager = LogManager()


def setup_production_logging():
    """Set up production-ready logging with rotation"""
    try:
        # Start cleanup scheduler
        log_manager.start_cleanup_scheduler()
        
        # Set up rotating handlers for key loggers
        loggers_to_setup = [
            'api_gateway',
            'pathway_engine', 
            'rag_system',
            'allocation_audit',
            'performance_monitor',
            'health_monitor'
        ]
        
        for logger_name in loggers_to_setup:
            logger = logging.getLogger(logger_name)
            
            # Add rotating handler
            rotating_handler = log_manager.setup_rotating_handler(logger_name)
            logger.addHandler(rotating_handler)
            
            # Add daily handler for long-term storage
            daily_handler = log_manager.setup_timed_handler(logger_name)
            logger.addHandler(daily_handler)
        
        api_logger.info("Production logging setup completed")
        
    except Exception as e:
        api_logger.error(f"Failed to setup production logging: {e}")


if __name__ == "__main__":
    # Test log management
    setup_production_logging()
    
    # Generate some test logs
    test_logger = logging.getLogger('test_logger')
    for i in range(100):
        test_logger.info(f"Test log message {i}")
    
    # Get statistics
    stats = log_manager.get_log_statistics()
    print(f"Log statistics: {stats}")
    
    # Cleanup
    log_manager.cleanup_old_logs()
    log_manager.stop_cleanup_scheduler()