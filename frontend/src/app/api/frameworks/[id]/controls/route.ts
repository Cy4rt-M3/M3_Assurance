import { NextResponse } from "next/server";

const FRAMEWORK_REGISTRY_URL =
  process.env.FRAMEWORK_REGISTRY_URL ?? "http://localhost:10006";

interface RegistryFramework {
  framework_id: string;
  name: string;
  version: string;
}

interface RegistryControl {
  control_id: string;
  framework_id: string;
  category: string;
  name: string;
  description: string;
  attack_mapping: string[];
}

interface RegistryCrosswalk {
  source_control_id: string;
  target_control_id: string;
  equivalence_level: string;
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const { searchParams } = new URL(request.url);

  const search = searchParams.get("search")?.toLowerCase() || undefined;
  const category = searchParams.get("category") || undefined;
  const page = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = Math.min(parseInt(searchParams.get("pageSize") || "50", 10), 200);

  const fwListRes = await fetch(`${FRAMEWORK_REGISTRY_URL}/frameworks`, {
    cache: "no-store",
  });
  const frameworks: RegistryFramework[] = fwListRes.ok ? await fwListRes.json() : [];
  const framework = frameworks.find((f) => f.framework_id === id);

  if (!framework) {
    return NextResponse.json(
      { error: "FRAMEWORK_NOT_FOUND", message: `No framework with id '${id}'` },
      { status: 404 }
    );
  }

  const controlsRes = await fetch(`${FRAMEWORK_REGISTRY_URL}/frameworks/${id}/controls`, {
    cache: "no-store",
  });

  if (!controlsRes.ok) {
    return NextResponse.json(
      { error: "REGISTRY_UNAVAILABLE", message: "Could not reach framework_registry" },
      { status: 502 }
    );
  }

  let controls: RegistryControl[] = await controlsRes.json();

  if (category) controls = controls.filter((c) => c.category === category);
  if (search) {
    controls = controls.filter(
      (c) =>
        c.control_id.toLowerCase().includes(search) ||
        c.name.toLowerCase().includes(search) ||
        c.description.toLowerCase().includes(search)
    );
  }

  const total = controls.length;
  const paged = controls.slice((page - 1) * pageSize, page * pageSize);

  // Fetch crosswalks for each control on this page in parallel.
  const crosswalksByControl = await Promise.all(
    paged.map(async (c) => {
      try {
        const res = await fetch(
          `${FRAMEWORK_REGISTRY_URL}/controls/${encodeURIComponent(c.control_id)}/crosswalks`,
          { cache: "no-store" }
        );
        if (!res.ok) return [] as string[];
        const data: RegistryCrosswalk[] = await res.json();
        return data.map((cw) => cw.target_control_id);
      } catch {
        return [] as string[];
      }
    })
  );

  return NextResponse.json({
    framework: { id: framework.framework_id, name: framework.name, version: framework.version },
    pagination: { page, pageSize, total },
    controls: paged.map((c, i) => ({
      controlId: c.control_id,
      controlName: c.name,
      description: c.description,
      functionDomain: null,
      category: c.category,
      keywords: c.attack_mapping,
      source: null,
      status: null,
      priority: null,
      parentControlId: null,
      controlLevel: null,
      controlObjective: null,
      controlType: null,
      evidenceRequired: null,
      evidenceType: [],
      evidenceSource: [],
      equivalentControls: crosswalksByControl[i],
      evidenceLink: null,
      owner: null,
      lastReviewed: null,
      notes: null,
    })),
  });
}