import axios, { AxiosInstance } from 'axios';
import authService from './auth.service'

interface Honeypot {
  id: string;
  name: string;
  type: string;
  status: 'running' | 'stopped' | 'error';
  platform: string;
  port: number;
  deployedAt: number;
  threatLevel: 'low' | 'medium' | 'high' | 'critical';
  interactionCount: number;
  lastInteraction?: number;
  config?: Record<string, string>;
}

interface InteractionEvent {
  id: string;
  honeypotId: string;
  honeypotName: string;
  timestamp: number;
  clientIp: string;
  clientPort: number;
  payloadSummary: string;
  severity: 'info' | 'warning' | 'critical';
  notes?: string;
}

interface DeceptionStats {
  totalHoneypots: number;
  activeHoneypots: number;
  totalInteractions: number;
  threatLevel: string;
  avgResponseTime: number;
  decoyModelsDeployed: number;
}

class DeceptionService {
  private apiClient: AxiosInstance;
  private baseURL = '/api/deception';

  constructor() {
    this.apiClient = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
        Authorization: authService.getAuthHeaders().Authorization,
      },
    });

    // Add interceptor to refresh token if needed
    this.apiClient.interceptors.response.use(
      response => response,
      error => {
        if (error.response?.status === 401) {
          authService.logout()
          try { console.debug('[DeceptionService] Dispatching jarvis:logout'); window.dispatchEvent(new CustomEvent('jarvis:logout')) } catch (e) { console.warn('Failed to dispatch logout event', e) }
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Get mock honeypot data for development
   */
  private getMockHoneypots(): Honeypot[] {
    const now = Date.now() / 1000;
    return [
      {
        id: 'hp-001',
        name: 'SSH Honeypot',
        type: 'SSH',
        status: 'running',
        platform: 'Atlas',
        port: 22,
        deployedAt: now - 86400 * 7,
        threatLevel: 'critical',
        interactionCount: 234,
        lastInteraction: now - 300,
      },
      {
        id: 'hp-002',
        name: 'Web Server Trap',
        type: 'HTTP',
        status: 'running',
        platform: 'HiSilicon',
        port: 8080,
        deployedAt: now - 86400 * 3,
        threatLevel: 'high',
        interactionCount: 156,
        lastInteraction: now - 600,
      },
      {
        id: 'hp-003',
        name: 'Database Decoy',
        type: 'PostgreSQL',
        status: 'running',
        platform: 'Atlas',
        port: 5432,
        deployedAt: now - 86400 * 14,
        threatLevel: 'medium',
        interactionCount: 89,
        lastInteraction: now - 1200,
      },
      {
        id: 'hp-004',
        name: 'FTP Service Trap',
        type: 'FTP',
        status: 'stopped',
        platform: 'HiSilicon',
        port: 21,
        deployedAt: now - 86400 * 2,
        threatLevel: 'low',
        interactionCount: 12,
      },
      {
        id: 'hp-005',
        name: 'TELNET Honeypot',
        type: 'TELNET',
        status: 'running',
        platform: 'Atlas',
        port: 23,
        deployedAt: now - 86400 * 5,
        threatLevel: 'high',
        interactionCount: 198,
        lastInteraction: now - 450,
      },
      {
        id: 'hp-006',
        name: 'SMB Trap',
        type: 'SMB',
        status: 'running',
        platform: 'HiSilicon',
        port: 445,
        deployedAt: now - 86400 * 1,
        threatLevel: 'critical',
        interactionCount: 456,
        lastInteraction: now - 120,
      },
    ];
  }

  /**
   * Get mock interaction events
   */
  private getMockEvents(): InteractionEvent[] {
    const now = Date.now() / 1000;
    const honeypots = this.getMockHoneypots();
    const events: InteractionEvent[] = [];

    honeypots.forEach(hp => {
      for (let i = 0; i < Math.min(hp.interactionCount, 5); i++) {
        events.push({
          id: `evt-${hp.id}-${i}`,
          honeypotId: hp.id,
          honeypotName: hp.name,
          timestamp: now - i * 3600,
          clientIp: `192.168.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}`,
          clientPort: Math.floor(Math.random() * 60000) + 1024,
          payloadSummary: `Attempted ${hp.type} connection with suspicious pattern`,
          severity: ['info', 'warning', 'critical'][Math.floor(Math.random() * 3)] as 'info' | 'warning' | 'critical',
          notes: `Interaction ${i + 1} for honeypot ${hp.name}`,
        });
      }
    });

    return events.sort((a, b) => b.timestamp - a.timestamp);
  }

  /**
   * List all honeypots
   */
  async listHoneypots(): Promise<Honeypot[]> {
    try {
      const response = await this.apiClient.get<Honeypot[]>('/honeypots');
      return response.data;
    } catch (error) {
      console.warn('Failed to fetch honeypots from API, using mock data:', error);
      return this.getMockHoneypots();
    }
  }

  /**
   * Get a specific honeypot by ID
   */
  async getHoneypot(id: string): Promise<Honeypot> {
    try {
      const response = await this.apiClient.get<Honeypot>(`/honeypots/${id}`);
      return response.data;
    } catch (error) {
      const mocks = this.getMockHoneypots();
      const found = mocks.find(h => h.id === id);
      if (found) return found;
      throw error;
    }
  }

  /**
   * Start a honeypot
   */
  async startHoneypot(id: string): Promise<Honeypot> {
    try {
      const response = await this.apiClient.post<Honeypot>(`/honeypots/${id}/start`);
      return response.data;
    } catch (error) {
      const mocks = this.getMockHoneypots();
      const found = mocks.find(h => h.id === id);
      if (found) {
        found.status = 'running';
        return found;
      }
      throw error;
    }
  }

  /**
   * Stop a honeypot
   */
  async stopHoneypot(id: string): Promise<Honeypot> {
    try {
      const response = await this.apiClient.post<Honeypot>(`/honeypots/${id}/stop`);
      return response.data;
    } catch (error) {
      const mocks = this.getMockHoneypots();
      const found = mocks.find(h => h.id === id);
      if (found) {
        found.status = 'stopped';
        return found;
      }
      throw error;
    }
  }

  /**
   * Create a new honeypot
   */
  async createHoneypot(config: Partial<Honeypot>): Promise<Honeypot> {
    const response = await this.apiClient.post<Honeypot>('/honeypots', config);
    return response.data;
  }

  /**
   * Delete a honeypot
   */
  async deleteHoneypot(id: string): Promise<void> {
    await this.apiClient.delete(`/honeypots/${id}`);
  }

  /**
   * List interaction events
   */
  async listInteractionEvents(honeypotId?: string): Promise<InteractionEvent[]> {
    try {
      const params = honeypotId ? { honeypot_id: honeypotId } : {};
      const response = await this.apiClient.get<InteractionEvent[]>('/events', { params });
      return response.data;
    } catch (error) {
      console.warn('Failed to fetch events from API, using mock data:', error);
      const events = this.getMockEvents();
      return honeypotId ? events.filter(e => e.honeypotId === honeypotId) : events;
    }
  }

  /**
   * Record an interaction event
   */
  async recordInteraction(
    honeypotId: string,
    clientIp: string,
    clientPort: number,
    payloadSummary: string,
    notes?: string
  ): Promise<InteractionEvent> {
    const response = await this.apiClient.post<InteractionEvent>(`/honeypots/${honeypotId}/interactions`, {
      client_ip: clientIp,
      client_port: clientPort,
      payload_summary: payloadSummary,
      notes,
    });
    return response.data;
  }

  /**
   * Get deception statistics
   */
  async getDeceptionStats(): Promise<DeceptionStats> {
    try {
      const response = await this.apiClient.get<DeceptionStats>('/stats');
      return response.data;
    } catch (error) {
      console.warn('Failed to fetch stats from API, using mock data:', error);
      const honeypots = this.getMockHoneypots();
      const events = this.getMockEvents();

      const threatLevelMap = { low: 1, medium: 2, high: 3, critical: 4 };
      const maxThreat = Math.max(...honeypots.map(hp => threatLevelMap[hp.threatLevel]));
      const threatNames = ['low', 'medium', 'high', 'critical'];

      return {
        totalHoneypots: honeypots.length,
        activeHoneypots: honeypots.filter(hp => hp.status === 'running').length,
        totalInteractions: events.length,
        threatLevel: threatNames[Math.min(maxThreat, 3)],
        avgResponseTime: Math.round(Math.random() * 500 + 100),
        decoyModelsDeployed: honeypots.filter(hp => hp.type === 'HTTP' || hp.type === 'SSH').length,
      };
    }
  }

  /**
   * Export honeypot logs to JSON
   */
  async exportLogs(): Promise<string> {
    try {
      const response = await this.apiClient.get<string>('/logs/export');
      return response.data;
    } catch (error) {
      console.warn('Failed to export logs from API');
      throw error;
    }
  }

  /**
   * Get honeypot attestation status (security-related)
   */
  async getAttestationStatus(honeypotId: string): Promise<Record<string, unknown>> {
    const response = await this.apiClient.get<Record<string, unknown>>(
      `/honeypots/${honeypotId}/attestation`
    );
    return response.data;
  }

  /**
   * Train decoy model for a honeypot
   */
  async trainDecoyModel(honeypotId: string, config: Record<string, string>): Promise<Record<string, unknown>> {
    const response = await this.apiClient.post<Record<string, unknown>>(
      `/honeypots/${honeypotId}/decoy-model`,
      config
    );
    return response.data;
  }

  /**
   * Get threat analytics for a time range
   */
  async getThreatAnalytics(startTime: number, endTime: number): Promise<Record<string, unknown>> {
    const response = await this.apiClient.get<Record<string, unknown>>('/analytics/threats', {
      params: { start_time: startTime, end_time: endTime },
    });
    return response.data;
  }
}

export default new DeceptionService();
