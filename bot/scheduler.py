from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import expire_old_deals
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

def start_scheduler():
    """Запуск планировщика задач"""
    scheduler.add_job(
        expire_old_deals,
        'interval',
        minutes=1,
        id='expire_deals'
    )
    
    scheduler.start()
    logger.info("Scheduler started")
