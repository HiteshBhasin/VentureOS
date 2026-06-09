from celery import shared_task
from  config.settings import app
from memory.supabase_client import engine
from core.orchestrator import Orchestrator

@shared_task(bind=True,max_retries =3 )
def queueing(task_id:str , user_input:str, llm):
    app.
    