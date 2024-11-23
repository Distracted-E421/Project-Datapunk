import * as d3 from 'd3';

declare module 'd3' {
    export * from 'd3-selection';
    export * from 'd3-scale';
    export * from 'd3-shape';
    export * from 'd3-array';
    export * from 'd3-axis';
    export * from 'd3-time';
    export * from 'd3-transition';

    export function select(selector: string | Element): Selection<Element, unknown, HTMLElement, any>;
    export function selectAll(selector: string): Selection<Element, unknown, HTMLElement, any>;
    
    export function scaleTime(): ScaleTime<number, number>;
    export function scaleLinear(): ScaleLinear<number, number>;
    
    export function line<Datum>(): Line<Datum>;
    export function area<Datum>(): Area<Datum>;
    export function arc<Datum>(): Arc<Datum>;
    
    export function axisBottom<Domain>(scale: Scale<Domain, number>): Axis<Domain>;
    export function axisLeft<Domain>(scale: Scale<Domain, number>): Axis<Domain>;
}

declare module 'd3-selection' {
    export interface BaseType extends Element {}
    
    export interface Selection<
        GElement extends BaseType,
        Datum,
        PElement extends BaseType,
        PDatum
    > {
        select(selector: string): Selection<GElement, Datum, PElement, PDatum>;
        selectAll(selector: string): Selection<BaseType, Datum, GElement, Datum>;
        attr(name: string, value: string | number | boolean | ((d: Datum) => string | number | boolean)): this;
        style(name: string, value: string | number | boolean | ((d: Datum) => string | number | boolean)): this;
        text(value: string | ((d: Datum) => string)): this;
        html(value: string): this;
        append<K extends keyof SVGElementTagNameMap>(name: K): Selection<SVGElementTagNameMap[K], Datum, PElement, PDatum>;
        append(name: string): Selection<BaseType, Datum, PElement, PDatum>;
        remove(): void;
        data<NewDatum>(data: NewDatum[]): Selection<GElement, NewDatum, PElement, PDatum>;
        join(enter: string): Selection<GElement, Datum, PElement, PDatum>;
        call(fn: (selection: Selection<GElement, Datum, PElement, PDatum>) => void): this;
        on(type: string, listener: (event: Event, d: Datum) => void): this;
    }
} 