import asyncio
import os
import psutil
import csv
from datetime import datetime
from loguru import logger

async def log_memory_usage(interval=60, filename="memory_log.csv"):

    process = psutil.Process(os.getpid())
    
    if not os.path.exists(filename):
        with open(filename, "w", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Memory_MB", "Memory_Percent"])
            
    logger.info(f"📊 Memory monitor started. Logging to {filename} every {interval}s")
    
    while True:
        try:

            mem_info = process.memory_info()
            mem_mb = mem_info.rss / 1024 / 1024 
            mem_percent = process.memory_percent()
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(filename, "a", newline="", encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, round(mem_mb, 2), round(mem_percent, 2)])
                
        except Exception as e:
            logger.error(f"Memory monitor error: {e}")
            
        await asyncio.sleep(interval)
