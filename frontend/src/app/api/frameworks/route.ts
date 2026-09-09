import { NextResponse } from "next/server";

const FRAMEWORK_REGISTRY_URL =
  process.env.FRAMEWORK_REGISTRY_URL ?? "http://localhost:10006";

interface RegistryFramework {
  framework_id: string;
  name: string;
  version: string;
  description: string;
  regions: string[];
}

export async function GET() {
  const res = await fetch(`${FRAMEWORK_REGISTRY_URL}/frameworks`, {
    cache: "no-store",
  });

  if (!res.ok) {
    return NextResponse.json(
      { error: "REGISTRY_UNAVAILABLE", message: "Could not reach framework_registry" },
      { status: 502 }
    );
  }

  const frameworks: RegistryFramework[] = await res.json();

  const withCounts = await Promise.all(
    frameworks.map(async (fw) => {
      const controlsRes = await fetch(
        `${FRAMEWORK_REGISTRY_URL}/frameworks/${fw.framework_id}/controls`,
        { cache: "no-store" }
      );
      const controls = controlsRes.ok ? await controlsRes.json() : [];
      return {
        id: fw.framework_id,
        name: fw.name,
        version: fw.version,
        controlCount: Array.isArray(controls) ? controls.length : 0,
      };
    })
  );

  return NextResponse.json({ frameworks: withCounts });
}