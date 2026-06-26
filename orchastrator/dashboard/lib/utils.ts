export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString();
}

export function formatTime(date: string | Date): string {
  return new Date(date).toLocaleTimeString();
}

export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'active':
    case 'completed':
    case 'success':
      return 'text-emerald-400';
    case 'running':
    case 'processing':
      return 'text-cyan-400';
    case 'error':
    case 'failed':
      return 'text-red-400';
    default:
      return 'text-zinc-400';
  }
}

export function truncate(text: string, length: number): string {
  return text.length > length ? `${text.slice(0, length)}...` : text;
}
