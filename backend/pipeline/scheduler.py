from apscheduler.schedulers.background import BackgroundScheduler
from .pipeline_manager import run_pipeline


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_pipeline, "interval", hours=1, id="pipeline")
    scheduler.start()
    print("[Scheduler] Pipeline scheduled every 1 hour.")
    return scheduler
