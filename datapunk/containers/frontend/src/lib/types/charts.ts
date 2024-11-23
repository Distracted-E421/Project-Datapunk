export interface ChartDimensions {
    width: number;
    height: number;
    margin: {
        top: number;
        right: number;
        bottom: number;
        left: number;
    };
}

export interface ChartOptions {
    title?: string;
    xLabel?: string;
    yLabel?: string;
    color?: string;
    interactive?: boolean;
    thresholds?: Array<{
        value: number;
        color: string;
    }>;
}

export interface ChartData {
    timestamp: string;
    value: number;
    [key: string]: any;
}

export interface ChartTooltip {
    x: number;
    y: number;
    content: string;
    visible: boolean;
} 