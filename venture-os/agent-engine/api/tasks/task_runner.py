from celery import shared_task
from  config.settings import app
from memory.supabase_client import engine
from core.orchestrator import Orchestrator

@shared_task(bind=True,max_retries =3 )
def queueing(task_id:str , user_input:str, llm):
    if app:
        celery_id = app.oid
        print(f"Task {task_id} is being processed by Celery worker with ID: {celery_id}")
        try:
            response  = (engine.table("tasks").insert({"celery_id": celery_id}).execute())
            
            if response== None:
                print(f"Failed to update task {task_id} with Celery ID: {response.text}")
            else:
                updated_response = engine.table("tasks").update({"celery_id": celery_id, "status": "processing"}).eq("id", task_id).execute()
                if updated_response != None:
                    orchastrator = Orchestrator(llm=llm)
                    orchastrator.process_user_request(user_input)
        except Exception as e:
            print(f"Failed to update task {task_id} status: {e}")
