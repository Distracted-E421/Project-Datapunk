export interface NavItem {
    id: string;
    label: string;
    path: string;
    icon: string;
    requiresAuth?: boolean;
    children?: NavItem[];
}

export const navigationConfig: NavItem[] = [
    {
        id: 'dashboard',
        label: 'Dashboard',
        path: '/',
        icon: 'dashboard'
    },
    {
        id: 'monitoring',
        label: 'System Health',
        path: '/monitoring',
        icon: 'monitoring',
        children: [
            {
                id: 'metrics',
                label: 'Performance Metrics',
                path: '/monitoring/metrics',
                icon: 'metrics'
            },
            {
                id: 'alerts',
                label: 'Alerts & Logs',
                path: '/monitoring/alerts',
                icon: 'alerts'
            }
        ]
    },
    {
        id: 'data',
        label: 'Data Management',
        path: '/data',
        icon: 'database',
        children: [
            {
                id: 'streams',
                label: 'Data Streams',
                path: '/data/streams',
                icon: 'stream'
            },
            {
                id: 'storage',
                label: 'Storage',
                path: '/data/storage',
                icon: 'storage'
            }
        ]
    },
    {
        id: 'services',
        label: 'Services',
        path: '/services',
        icon: 'services',
        children: [
            {
                id: 'lake',
                label: 'Lake Service',
                path: '/services/lake',
                icon: 'lake'
            },
            {
                id: 'stream',
                label: 'Stream Service',
                path: '/services/stream',
                icon: 'stream'
            },
            {
                id: 'nexus',
                label: 'Nexus Gateway',
                path: '/services/nexus',
                icon: 'gateway'
            }
        ]
    },
    {
        id: 'settings',
        label: 'Settings',
        path: '/settings',
        icon: 'settings',
        requiresAuth: true
    }
]; 