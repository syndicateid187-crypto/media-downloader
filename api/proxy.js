export const config = {
    runtime: 'edge',
};

export default async function (request) {
    const { searchParams } = new URL(request.url);
    const url = searchParams.get('url');
    const filename = searchParams.get('filename') || 'download.mp4';

    if (!url) {
        return new Response('URL is required', { status: 400 });
    }

    try {
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.pinterest.com/'
            }
        });

        if (!response.ok) {
            return new Response(`Failed to fetch media: ${response.statusText}`, { status: response.status });
        }

        const { body, headers } = response;
        const contentType = headers.get('Content-Type') || 'application/octet-stream';

        return new Response(body, {
            status: 200,
            headers: {
                'Content-Type': contentType,
                'Content-Disposition': `attachment; filename="${filename}"`,
                'Access-Control-Allow-Origin': '*',
            },
        });
    } catch (error) {
        console.error('Proxy error:', error);
        return new Response(`Proxy error: ${error.message}`, { status: 500 });
    }
}
