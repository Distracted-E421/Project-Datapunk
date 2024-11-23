import type { RequestHandler } from '@sveltejs/kit';

export const GET: RequestHandler = async () => {
    try {
        // Add any additional health checks here
        return new Response(JSON.stringify({ status: 'healthy' }), {
            status: 200,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        return new Response(JSON.stringify({ 
            status: 'unhealthy', 
            error: errorMessage 
        }), {
            status: 503,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }
}; 