import { Agent, CreateAgentRequest } from '@/types/agent';
import { Task, CreateTaskRequest } from '@/types/task';

// Agent APIs
export async function getAgents(): Promise<Agent[]>;
export async function getAgent(id: string): Promise<Agent>;
export async function createAgent(data: CreateAgentRequest): Promise<Agent>;
export async function updateAgent(id: string, data: Partial<CreateAgentRequest>): Promise<Agent>;
export async function deleteAgent(id: string): Promise<void>;

// Task APIs
export async function getTasks(agentId?: string): Promise<Task[]>;
export async function getTask(id: string): Promise<Task>;
export async function createTask(data: CreateTaskRequest): Promise<Task>;
export async function updateTask(id: string, data: Partial<CreateTaskRequest>): Promise<Task>;
export async function deleteTask(id: string): Promise<void>;

// Authentication APIs
export async function login(email: string, password: string): Promise<any>;
export async function signup(email: string, password: string, name: string): Promise<any>;
export async function logout(): Promise<void>;
