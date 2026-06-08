from typing import Any
from collections import deque

class TaskQueue:
    def __init__(self):
        self._list = deque()
        
    
    def add(self,element:Any)->None:
        self._list.append(element)
        self._add_to_db(element)

    def _add_to_db(self,element:Any) ->None:  
        pass # @need to add the DB logic to add the task to the DB
    
    def highest_priority(self)->Any:
        return self._list.popleft()
    
    
    
    def background_wrokers(self):