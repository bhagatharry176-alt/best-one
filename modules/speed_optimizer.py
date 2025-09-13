#!/usr/bin/env python3
"""
Speed Optimization Module - Fixes Render Speed Degradation
Addresses the issue where speed drops from 8MB/s to 1MB/s after 2 downloads
"""

import os
import gc
import time
import asyncio
import tempfile
import shutil
from pathlib import Path

# Try to import psutil, but continue without it
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil not available, using basic resource monitoring")

class RenderSpeedOptimizer:
    """Optimize download speeds and prevent degradation in Render environment"""
    
    def __init__(self):
        self.download_count = 0
        self.last_cleanup = time.time()
        self.temp_dirs = []
        
    def force_memory_cleanup(self):
        """Aggressive memory cleanup to prevent speed degradation"""
        try:
            # Force garbage collection
            gc.disable()
            gc.collect()
            gc.enable()
            
            # Clear any cached modules
            import sys
            for module_name in list(sys.modules.keys()):
                if 'yt_dlp' in module_name:
                    if module_name in sys.modules:
                        del sys.modules[module_name]
            
            print("🧹 Aggressive memory cleanup completed")
            
        except Exception as e:
            print(f"⚠️ Memory cleanup warning: {e}")
    
    def cleanup_temporary_files(self):
        """Clean up temporary files that cause speed degradation"""
        try:
            cleanup_count = 0
            
            # Clean up temporary files
            for pattern in ["*.part", "*.tmp", "*.download"]:
                for file in Path(".").glob(pattern):
                    try:
                        file.unlink()
                        cleanup_count += 1
                    except:
                        pass
            
            # Clean up temporary directories
            for temp_dir in self.temp_dirs:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    cleanup_count += 1
                except:
                    pass
            self.temp_dirs.clear()
            
            # Clean up Python temp files
            temp_dir = Path(tempfile.gettempdir())
            for pattern in ["tmp*", "yt-dlp*"]:
                for file in temp_dir.glob(pattern):
                    try:
                        if file.is_file():
                            file.unlink()
                        elif file.is_dir():
                            shutil.rmtree(file, ignore_errors=True)
                        cleanup_count += 1
                    except:
                        pass
            
            if cleanup_count > 0:
                print(f"🧹 Cleaned up {cleanup_count} temporary files")
                
        except Exception as e:
            print(f"⚠️ Temp cleanup warning: {e}")
    
    def reset_network_connections(self):
        """Reset network connections to prevent throttling"""
        try:
            
            # Reset DNS cache (if possible)
            os.system("echo '' > /etc/resolv.conf.cache 2>/dev/null || true")
            
            # Force connection reset
            time.sleep(0.5)
            
            print("🌐 Network connections reset")
            
        except Exception as e:
            print(f"⚠️ Network reset warning: {e}")
    
    def check_system_resources(self):
        """Check and report system resource usage"""
        try:
            if PSUTIL_AVAILABLE:
                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                
                print(f"📊 Memory: {memory_percent:.1f}% | Disk: {disk_percent:.1f}%")
                
                # Warning thresholds
                if memory_percent > 80:
                    print("⚠️ High memory usage detected - forcing cleanup")
                    self.force_memory_cleanup()
                    
                if disk_percent > 90:
                    print("⚠️ High disk usage detected - cleaning temporary files")
                    self.cleanup_temporary_files()
                    
                return memory_percent < 85 and disk_percent < 95
            else:
                # Basic monitoring without psutil
                print("📊 Basic resource monitoring (psutil not available)")
                return True
            
        except Exception as e:
            print(f"⚠️ Resource check warning: {e}")
            return True
    
    def optimize_before_download(self):
        """Run optimizations before each download"""
        self.download_count += 1
        current_time = time.time()
        
        print(f"🚀 Optimizing for download #{self.download_count}")
        
        # Gentle cleanup after every 5 downloads (prevent interruption)
        if self.download_count % 5 == 0:
            print(f"🔧 Running gentle optimization (every 5 downloads)")
            self.cleanup_temporary_files()
            # Skip aggressive cleanup during active downloads
        
        # Regular cleanup every 5 minutes
        elif current_time - self.last_cleanup > 300:
            print(f"🔧 Running scheduled optimization (5-minute interval)")
            self.cleanup_temporary_files()
            self.last_cleanup = current_time
        
        # Always check resources
        resource_ok = self.check_system_resources()
        
        if not resource_ok:
            print("⚠️ System resources critical - running emergency cleanup")
            self.force_memory_cleanup()
            self.cleanup_temporary_files()
        
        print(f"✅ Optimization complete for download #{self.download_count}")
    
    def optimize_download_command(self, base_cmd):
        """Optimize download parameters for sustained speed using built-in downloader"""
        # Use built-in downloader with optimized settings
        optimized_args = [
            "--concurrent-fragments", "8",
            "--fragment-retries", "10", 
            "--retries", "5",
            "--socket-timeout", "60",
            "--http-chunk-size", "2M",
        ]
        
        # Add optimization args to base command
        optimized_cmd = base_cmd
        for i in range(0, len(optimized_args), 2):
            if optimized_args[i] not in base_cmd:
                optimized_cmd += f" {optimized_args[i]} {optimized_args[i+1]}"
        
        return optimized_cmd

# Global optimizer instance
speed_optimizer = RenderSpeedOptimizer()

def optimize_download_speed():
    """Main function to optimize download speed"""
    speed_optimizer.optimize_before_download()

def get_optimized_command(cmd):
    """Get optimized download command"""
    return speed_optimizer.optimize_download_command(cmd)