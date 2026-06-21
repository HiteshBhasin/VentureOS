# Background worker — manual implementation (Celery removed)
# This file will contain the poll-claim-execute loop that replaces Celery.
from memory.supabase_client import engine 

class Background_runner:
    
    def __init__(self):
        pass
    
    def query_check(self):
        raw_query = """
            SELECT id FROM tasks
            WHERE status = 'pending' AND visible_at <= NOW()
            ORDER BY
                CASE priority
                    WHEN 'critical' THEN 1
                    WHEN 'high'     THEN 2
                    WHEN 'medium'   THEN 3
                    WHEN 'low'      THEN 4
                END ASC,
                created_at ASC
            LIMIT 1;
        """
        responce = engine.postgrest.rpc("execute_sql", {"query":raw_query}).execute()

        
    
    
