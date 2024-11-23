declare module 'd3' {
    export * from 'd3-selection';
    export * from 'd3-scale';
    export * from 'd3-shape';
    export * from 'd3-array';
    export * from 'd3-axis';
    export * from 'd3-time';
    export * from 'd3-transition';
}

declare module 'd3-selection' {
    export interface BaseType {}
    export interface Selection<
        GElement extends BaseType,
        Datum,
        PElement extends BaseType,
        PDatum
    > {
        select: any;
        selectAll: any;
        attr: any;
        style: any;
        text: any;
        append: any;
        remove: any;
    }
}

declare module 'd3-scale' {
    export interface ScaleTime<Range, Output> {
        domain: any;
        range: any;
        invert: any;
    }
    export interface ScaleLinear<Range, Output> {
        domain: any;
        range: any;
    }
} 