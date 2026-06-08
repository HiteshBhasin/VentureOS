'use client';

import { useState, useEffect} from 'react';
import { Task } from '@/types/task';
export function TaskShowInfo(task:Task){

    const [showInfo, setShowInfo] = useState<Task|null>(null);

    const handleClick = ()=>{
        const userData: Task = {
            "id":task.id,
            "title": task.title,
            "description":task.description,
            "status":task.status,
            "created_at":task.created_at,
            "completed_at":task.created_at,
            "priority":task.priority,
            "updated_at":task.updated_at,
            "tags":task.tags,
            "agent_id":task.agent_id,
            "progress":task.progress
        }
        

        setShowInfo(userData)
    }

    useEffect(()=>{
        if(showInfo){
            console.log("user information", showInfo)
        }
    },[showInfo])
    return handleClick;

};