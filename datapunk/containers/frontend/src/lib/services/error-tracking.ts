import type { Alert } from '$lib/types/monitoring';
import { environment } from '$lib/config/environment';

interface ErrorReport {
    error: Error;
    context?: Record<string, any>;
    timestamp: string;
}

class ErrorTrackingService {
    private alerts: Alert[] = [];
    private errorCallback?: (alert: Alert) => void;

    public initialize(onError: (alert: Alert) => void) {
        this.errorCallback = onError;
        
        window.addEventListener('error', (event) => {
            this.handleError(event.error);
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError(event.reason);
        });
    }

    public handleError(error: Error, context?: Record<string, any>) {
        const report: ErrorReport = {
            error,
            context,
            timestamp: new Date().toISOString()
        };

        console.error('Error tracked:', report);

        const alert: Alert = {
            id: crypto.randomUUID(),
            severity: 'critical',
            title: 'Application Error',
            message: error.message,
            timestamp: report.timestamp
        };

        this.alerts.push(alert);
        this.errorCallback?.(alert);

        // In production, send to logging service
        if (environment.NODE_ENV === 'production') {
            this.sendToLoggingService(report);
        }
    }

    private async sendToLoggingService(report: ErrorReport) {
        try {
            await fetch('/api/logs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(report)
            });
        } catch (error) {
            console.error('Failed to send error report:', error);
        }
    }

    public getRecentAlerts(): Alert[] {
        return this.alerts.slice(-10);
    }
}

export const errorTracking = new ErrorTrackingService(); 