declare module 'd3' {
    export * from 'd3-selection';
    export * from 'd3-scale';
    export * from 'd3-array';
    export * from 'd3-shape';
    export * from 'd3-axis';
    export * from 'd3-time';
    export * from 'd3-transition';
    
    // Add missing type definitions
    export function select(selector: string | Element): Selection<Element, unknown, HTMLElement, any>;
    export function selectAll(selector: string): Selection<Element, unknown, HTMLElement, any>;
    
    export function scaleTime(): ScaleTime<number, number>;
    export function scaleLinear(): ScaleLinear<number, number>;
    export function arc<Datum>(): Arc<any, Datum>;
    export function line<Datum>(): Line<Datum>;
    export function area<Datum>(): Area<Datum>;
    
    export function axisBottom<Domain>(scale: Scale<Domain, number>): Axis<Domain>;
    export function axisLeft<Domain>(scale: Scale<Domain, number>): Axis<Domain>;
    
    export function extent<T, V>(
        array: T[],
        accessor: (datum: T) => V
    ): [V, V] | [undefined, undefined];
    
    export function max<T>(
        array: T[],
        accessor: (datum: T) => number
    ): number | undefined;
}

// Add BaseType interface
export interface BaseType extends Element {}

// Add Selection interface with proper types
export interface Selection<
    GElement extends BaseType,
    Datum,
    PElement extends BaseType,
    PDatum
> {
    select(selector: string): Selection<GElement, Datum, PElement, PDatum>;
    selectAll(selector: string): Selection<BaseType, Datum, GElement, Datum>;
    append<K extends keyof SVGElementTagNameMap>(
        name: K
    ): Selection<SVGElementTagNameMap[K], Datum, PElement, PDatum>;
    append(name: string): Selection<BaseType, Datum, PElement, PDatum>;
    attr(name: string, value: string | number | boolean | ((d: Datum) => string | number | boolean)): this;
    style(name: string, value: string | number | boolean | ((d: Datum) => string | number | boolean)): this;
    text(value: string | ((d: Datum) => string)): this;
    html(value: string | ((d: Datum) => string)): this;
    datum<T>(value: T): Selection<GElement, T, PElement, PDatum>;
    data<T>(data: T[]): Selection<GElement, T, PElement, PDatum>;
    merge(other: Selection<GElement, Datum, PElement, PDatum>): this;
    transition(): Transition<GElement, Datum, PElement, PDatum>;
    remove(): void;
    on(type: string, listener: (event: Event, d: Datum) => void): this;
}

// Add Scale interfaces
export interface Scale<Domain, Range> {
    (value: Domain): Range;
    domain(domain: Domain[]): this;
    range(range: Range[]): this;
}

export interface ScaleTime<Range, Output> extends Scale<Date | number, Range> {
    invert(value: Range): Date;
}

export interface ScaleLinear<Range, Output> extends Scale<number, Range> {}

// Add Line interface
export interface Line<Datum> {
    (data: Datum[]): string | null;
    x(accessor: (d: Datum) => number): this;
    y(accessor: (d: Datum) => number): this;
}

// Add Area interface
export interface Area<Datum> {
    (data: Datum[]): string | null;
    x(accessor: (d: Datum) => number): this;
    y0(accessor: (d: Datum) => number): this;
    y1(accessor: (d: Datum) => number): this;
}

// Add Axis interface
export interface Axis<Domain> {
    (context: Selection<SVGGElement, unknown, HTMLElement, any>): void;
    scale(): Scale<Domain, number>;
    scale(scale: Scale<Domain, number>): this;
    ticks(count?: number): this;
    tickFormat(format: (d: Domain) => string): this;
}

// Add Transition interface
export interface Transition<
    GElement extends BaseType,
    Datum,
    PElement extends BaseType,
    PDatum
> extends Selection<GElement, Datum, PElement, PDatum> {
    duration(milliseconds: number): this;
} 