declare module 'd3' {
    export * from 'd3-selection';
    export * from 'd3-scale';
    export * from 'd3-shape';
    export * from 'd3-array';
    export * from 'd3-axis';
    export * from 'd3-time';
    export * from 'd3-transition';
    
    // Selection functions
    export function select(selector: string | Element): Selection<Element, unknown, HTMLElement, any>;
    export function selectAll(selector: string): Selection<Element, unknown, HTMLElement, any>;
    
    // Scale factories
    export function scaleTime(): ScaleTime<number, number>;
    export function scaleLinear(): ScaleLinear<number, number>;
    
    // Shape generators
    export function line<Datum>(): Line<Datum>;
    export function arc<Datum>(): Arc<Datum>;
    export function area<Datum>(): Area<Datum>;
    
    // Axis factories
    export function axisBottom<Domain>(scale: Scale<Domain, number>): Axis<Domain>;
    export function axisLeft<Domain>(scale: Scale<Domain, number>): Axis<Domain>;
    
    // Array helpers
    export function extent<T, V>(
        array: T[],
        accessor: (datum: T) => V
    ): [V, V] | [undefined, undefined];
    
    export function max<T>(
        array: T[],
        accessor: (datum: T) => number
    ): number | undefined;
}

// Selection interface
export interface Selection<
    GElement extends BaseType,
    Datum,
    PElement extends BaseType,
    PDatum
> {
    select<DescElement extends BaseType>(selector: string): Selection<DescElement, Datum, PElement, PDatum>;
    selectAll<DescElement extends BaseType, NewDatum>(selector: string): Selection<DescElement, NewDatum, GElement, Datum>;
    append<K extends keyof SVGElementTagNameMap>(name: K): Selection<SVGElementTagNameMap[K], Datum, PElement, PDatum>;
    append(name: string): Selection<BaseType, Datum, PElement, PDatum>;
    attr(name: string, value: string | number | boolean | ((d: Datum) => string | number | boolean)): this;
    style(name: string, value: string | number | boolean | ((d: Datum) => string | number | boolean)): this;
    text(value: string | ((d: Datum) => string)): this;
    html(value: string | ((d: Datum) => string)): this;
    data<NewDatum>(data: NewDatum[]): Selection<GElement, NewDatum, PElement, PDatum>;
    datum<NewDatum>(value: NewDatum): Selection<GElement, NewDatum, PElement, PDatum>;
    enter(): Selection<GElement, Datum, PElement, PDatum>;
    exit(): Selection<GElement, Datum, PElement, PDatum>;
    merge(selection: Selection<GElement, Datum, PElement, PDatum>): this;
    transition(): Transition<GElement, Datum, PElement, PDatum>;
    remove(): void;
    call(fn: (selection: Selection<GElement, Datum, PElement, PDatum>) => void): this;
    on(type: string, listener: (event: Event, d: Datum) => void): this;
}

// Transition interface
export interface Transition<
    GElement extends BaseType,
    Datum,
    PElement extends BaseType,
    PDatum
> {
    duration(ms: number): this;
    style(name: string, value: string | number | boolean | ((d: Datum) => string | number | boolean)): this;
}

// Base interfaces
export interface BaseType extends Element {}

export interface Scale<Domain, Range> {
    (value: Domain): Range;
    domain(domain: Domain[]): this;
    range(range: Range[]): this;
}

export interface ScaleTime<Range, Output> extends Scale<Date | number, Range> {
    invert(value: Range): Date;
}

export interface ScaleLinear<Range, Output> extends Scale<number, Range> {}

export interface Line<Datum> {
    (data: Datum[]): string | null;
    x(accessor: (d: Datum) => number): this;
    y(accessor: (d: Datum) => number): this;
}

export interface Arc<Datum> {
    (d: Datum): string | null;
    innerRadius(radius: number | ((d: Datum) => number)): this;
    outerRadius(radius: number | ((d: Datum) => number)): this;
    startAngle(angle: number | ((d: Datum) => number)): this;
    endAngle(angle: number | ((d: Datum) => number)): this;
}

export interface Area<Datum> {
    (data: Datum[]): string | null;
    x(accessor: (d: Datum) => number): this;
    y0(accessor: (d: Datum) => number): this;
    y1(accessor: (d: Datum) => number): this;
}

export interface Axis<Domain> {
    (selection: Selection<SVGGElement, unknown, HTMLElement, any>): void;
    scale(): Scale<Domain, number>;
    scale(scale: Scale<Domain, number>): this;
    ticks(count?: number): this;
    tickFormat(format: (d: Domain) => string): this;
}

// Add at the top level of the file
export interface WebSocketMessageEvent extends Event {
    data: any;
} 