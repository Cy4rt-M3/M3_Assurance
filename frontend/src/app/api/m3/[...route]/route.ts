import { NextRequest, NextResponse } from 'next/server';

/**
 * M3 Assurance API gateway.
 *
 * Proxies browser requests to the seven backend FastAPI services so the
 * dashboard never needs to know service ports or deal with CORS.
 *
 * Route shape:  /api/m3/{service}/{...rest}
 *
 *   registry  -> /{rest}            (frameworks, controls, crosswalks)
 *   mapping   -> /api/v1/{rest}     (control mapping service)
 *   evidence  -> /api/v1/{rest}     (evidence aggregator service)
 *   gaps      -> /api/v1/{rest}     (gap analyzer service)
 *   scorer    -> /api/v1/{rest}     (resilience scorer service)
 *   reports   -> /api/v1/{rest}     (report generator service)
 *   publish   -> /api/v1/{rest}     (report publisher service)
 *
 * Service bases default to http://127.0.0.1:<port> and can be overridden
 * with M3_BASE_<SERVICE> (e.g. M3_BASE_EVIDENCE) or the ports with
 * M3_PORT_<SERVICE>.
 */

const SERVICE_PORTS: Record<string, number> = {
  mapping: 10001,
  evidence: 10002,
  gaps: 10003,
  scorer: 10004,
  reports: 10005,
  registry: 10006,
  publish: 10007,
};

const ROOT_PATH_SERVICES = new Set(['registry']);

type RouteContext = { params: Promise<{ route: string[] }> };

function resolveBase(service: string): string | null {
  const envBase = process.env[`M3_BASE_${service.toUpperCase()}`];
  if (envBase) return envBase.replace(/\/+$/, '');
  const envPort = process.env[`M3_PORT_${service.toUpperCase()}`];
  const port = envPort ?? SERVICE_PORTS[service];
  if (!port) return null;
  return `http://127.0.0.1:${port}`;
}

function buildUrl(
  base: string,
  service: string,
  rest: string[],
  search: string,
): string {
  const joined = rest.join('/');
  const root = ROOT_PATH_SERVICES.has(service) ? `/${joined}` : `/api/v1/${joined}`;
  return `${base}${root}${search}`;
}

async function proxy(
  request: NextRequest,
  context: RouteContext,
): Promise<NextResponse> {
  const { route } = await context.params;
  const [service, ...rest] = route;

  const base = resolveBase(service);
  if (!base) {
    return NextResponse.json(
      { detail: `Unknown M3 service '${service}'` },
      { status: 404 },
    );
  }

  const url = buildUrl(base, service, rest, request.nextUrl.search);
  const headers: Record<string, string> = {};
  const contentType = request.headers.get('content-type');
  if (contentType) headers['content-type'] = contentType;

  const init: RequestInit = { method: request.method, headers };
  if (request.method === 'POST' || request.method === 'PUT') {
    init.body = await request.text();
  }

  try {
    const upstream = await fetch(url, init);
    const contentType = upstream.headers.get('content-type') ?? '';
    if (contentType.includes('application/json')) {
      const text = await upstream.text();
      let body: unknown;
      try {
        body = text ? JSON.parse(text) : null;
      } catch {
        body = text;
      }
      return NextResponse.json(body, { status: upstream.status });
    }

    const headers = new Headers();
    headers.set('content-type', contentType);
    const disposition = upstream.headers.get('content-disposition');
    if (disposition) headers.set('content-disposition', disposition);
    return new Response(upstream.body, { status: upstream.status, headers });
  } catch (error) {
    return NextResponse.json(
      {
        detail: `M3 gateway error for /${service}/${rest.join('/')}: ${
          error instanceof Error ? error.message : String(error)
        }`,
      },
      { status: 502 },
    );
  }
}

export async function GET(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}