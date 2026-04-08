const IP = process.env.EXPO_PUBLIC_IP ?? '10.194.183.127';
const PORT = process.env.EXPO_PUBLIC_PORT ?? '8000';

export const API_BASE = `http://${IP}:${PORT}`;
export async function getAlertHistory(hubId: number, limit: number = 20) {
    const response = await fetch(`${API_BASE}/api/hubs/${hubId}/alerts?limit=${limit}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch alert history: ${response.status} ${response.statusText}`);
    }
    return response.json();
}
