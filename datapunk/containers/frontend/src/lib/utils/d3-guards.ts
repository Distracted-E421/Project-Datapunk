import type { 
    Selection, 
    BaseType,
    ScaleTime,
    ScaleLinear,
    Arc as D3Arc,
    Line as D3Line,
    Area as D3Area,
    Axis as D3Axis
} from 'd3';

export interface D3Error extends Error {
    type: 'selection' | 'scale' | 'data' | 'render' | 'transition';
    context?: string;
    originalError?: Error;
}

export type D3Selection<GElement extends BaseType = BaseType> = 
    Selection<GElement, unknown, HTMLElement, any>;

export interface D3Transition<GElement extends BaseType = BaseType> {
    duration(ms: number): this;
    style(name: string, value: string | number): this;
}

export interface TooltipSelection {
    transition(): D3Transition<HTMLDivElement>;
    html(value: string): this;
    remove(): void;
    style(
        name: string,
        value: string | number | null | ((d: unknown) => string | number),
        priority?: 'important' | null
    ): this;
    attr(name: string, value: string | number | boolean | ((d: unknown) => string | number | boolean)): this;
}

// Type guards
export function isD3Selection(value: unknown): value is D3Selection {
    return value !== null && 
           typeof value === 'object' && 
           'select' in value &&
           'selectAll' in value;
}

export function isScaleTime(value: unknown): value is ScaleTime<number, number> {
    return value !== null && 
           typeof value === 'object' && 
           'domain' in value &&
           'range' in value &&
           'invert' in value;
}

export function isScaleLinear(value: unknown): value is ScaleLinear<number, number> {
    return value !== null && 
           typeof value === 'object' && 
           'domain' in value &&
           'range' in value;
}

export function isArc<T>(value: unknown): value is D3Arc<any, T> {
    return value !== null && 
           typeof value === 'object' && 
           'innerRadius' in value &&
           'outerRadius' in value;
}

export function isLine<T>(value: unknown): value is D3Line<T> {
    return value !== null && 
           typeof value === 'object' && 
           'x' in value &&
           'y' in value;
}

export function isArea<T>(value: unknown): value is D3Area<T> {
    return value !== null && 
           typeof value === 'object' && 
           'x' in value &&
           'y0' in value &&
           'y1' in value;
}

export function isAxis(value: unknown): value is D3Axis<number | Date | string> {
    return value !== null && 
           typeof value === 'object' && 
           'scale' in value &&
           'ticks' in value;
}

export function createD3Error(
    message: string,
    type: D3Error['type'],
    context?: string,
    originalError?: Error
): D3Error {
    const error = new Error(message) as D3Error;
    error.type = type;
    error.context = context;
    error.originalError = originalError;
    return error;
}

export function handleD3Error(error: unknown, context: string): D3Error {
    if (error instanceof Error) {
        return createD3Error(
            error.message,
            'render',
            context,
            error
        );
    }
    return createD3Error(
        'Unknown D3 error',
        'render',
        context
    );
}

export function validateD3Selection<T extends BaseType>(
    selection: unknown,
    context: string
): asserts selection is Selection<T, unknown, HTMLElement, any> {
    if (!isD3Selection(selection)) {
        throw createD3Error(
            'Invalid D3 selection',
            'selection',
            context
        );
    }
}

export function validateScaleTime(
    scale: unknown,
    context: string
): asserts scale is ScaleTime<number, number> {
    if (!isScaleTime(scale)) {
        throw createD3Error(
            'Invalid time scale',
            'scale',
            context
        );
    }
}

export function validateScaleLinear(
    scale: unknown,
    context: string
): asserts scale is ScaleLinear<number, number> {
    if (!isScaleLinear(scale)) {
        throw createD3Error(
            'Invalid linear scale',
            'scale',
            context
        );
    }
}

export function isTooltipSelection(value: unknown): value is TooltipSelection {
    return isD3Selection(value) && 
           'transition' in value &&
           'html' in value;
}

export function validateTooltipSelection(
    selection: unknown,
    context: string
): asserts selection is TooltipSelection {
    if (!isTooltipSelection(selection)) {
        throw createD3Error(
            'Invalid tooltip selection',
            'selection',
            context
        );
    }
} 