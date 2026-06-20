from typing import Any
from collections import deque
from supabase import create_client, Client
from pathlib import Path
import os
from dotenv import load_dotenv
# Load from root .env (VentureOS/.env)
load_dotenv(dotenv_path=Path(__file__).resolve().parents[3] / ".env")

class TaskQueue:
    def __init__(self):
        self._list = deque()
        
    
    def add(self,element:Any)->None:
        self._list.append(element)
        self._add_to_db(element)

    def _add_to_db(self,element:dict) ->None:  
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

        if not SUPABASE_URL or not SUPABASE_KEY:
            raise EnvironmentError(
        "SUPABASE_URL and SUPABASE_KEY must be set in your .env file.")

        try :
            engine : Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            engine.table("tasks")
            
        except:
    
    def highest_priority(self)->Any:
        return self._list.popleft()
    
    
    
    def background_wrokers(self):