import { writable } from 'svelte/store';
import type { ChartData } from '$lib/types/charts';

interface ChartState {
    timeSeriesData: ChartData[];
    gaugeData: {
        cpu: number;
        memory: number;
        disk: number;
    };
    lastUpdate: Date;
}

function createChartStore() {
    const { subscribe, set, update } = writable<ChartState>({
        timeSeriesData: [],
        gaugeData: {
            cpu: 0,
            memory: 0,
            disk: 0
        },
        lastUpdate: new Date()
    });

    return {
        subscribe,
        updateTimeSeries: (data: ChartData[]) => update(state => ({
            ...state,
            timeSeriesData: data,
            lastUpdate: new Date()
        })),
        updateGauges: (gauges: Partial<ChartState['gaugeData']>) => update(state => ({
            ...state,
            gaugeData: { ...state.gaugeData, ...gauges },
            lastUpdate: new Date()
        })),
        reset: () => set({
            timeSeriesData: [],
            gaugeData: { cpu: 0, memory: 0, disk: 0 },
            lastUpdate: new Date()
        })
    };
}

export const chartStore = createChartStore(); 