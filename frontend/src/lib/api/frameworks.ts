const FRAMEWORK_API_URL =
  process.env.NEXT_PUBLIC_FRAMEWORK_API_URL || "http://localhost:10006";

  const MAPPING_API_URL =
    process.env.NEXT_PUBLIC_MAPPING_API_URL || "http://localhost:10001";
export async function getFrameworks() {
  const response = await fetch(`${FRAMEWORK_API_URL}/frameworks`);

  if (!response.ok) {
    throw new Error("Failed to fetch frameworks");
  }

  return response.json();
}

export async function getFrameworkControls(frameworkId: string) {
  const response = await fetch(
    `${FRAMEWORK_API_URL}/frameworks/${encodeURIComponent(frameworkId)}/controls`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch controls");
  }

  return response.json();
}

export async function getControlMappings(controlId: string) {
  const response = await fetch(
    `${MAPPING_API_URL}/controls/${encodeURIComponent(controlId)}/mappings`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch mappings for ${controlId}`);
  }

  return response.json();
}


// const API_BASE_URL = "http://127.0.0.1:10001";

// export async function getFrameworks() {
//   const response = await fetch(`${API_BASE_URL}/frameworks`);

//   if (!response.ok) {
//     throw new Error("Failed to fetch frameworks");
//   }

//   return response.json();
// }

// export async function getFrameworkControls(frameworkId: string) {
//   const response = await fetch(
//     `${API_BASE_URL}/frameworks/${encodeURIComponent(frameworkId)}/controls`
//   );

//   if (!response.ok) {
//     throw new Error("Failed to fetch controls");
//   }

//   return response.json();
// }
// export async function getControlMappings(controlId: string) {
//   const response = await fetch(
//     `${API_BASE_URL}/controls/${encodeURIComponent(controlId)}/mappings`
//   );

//   if (!response.ok) {
//     throw new Error(`Failed to fetch mappings for ${controlId}`);
//   }

//   return response.json();
// }

// export async function getControlMappings(controlId: string) {
//   const response = await fetch(
//     `${API_BASE_URL}/mappings/${encodeURIComponent(controlId)}`
//   );

//   if (!response.ok) {
//     throw new Error(`Failed to fetch mappings for ${controlId}`);
//   }

//   return response.json();
// }


// const API_BASE_URL = "http://127.0.0.1:8000";

// export async function getFrameworks() {
//   const response = await fetch(`${API_BASE_URL}/frameworks`);

//   if (!response.ok) {
//     throw new Error("Failed to fetch frameworks");
//   }

//   return response.json();
// }

// export async function getFrameworkControls(frameworkId: string) {
//   const response = await fetch(
//     `${API_BASE_URL}/frameworks/${frameworkId}/controls`
//   );

//   if (!response.ok) {
//     throw new Error("Failed to fetch controls");
//   }

//   return response.json();
// }
// export async function getControlMappings(controlId: string) {
//   const response = await fetch(
//     `${API_BASE_URL}/controls/${encodeURIComponent(controlId)}/mappings`
//   );

//   if (!response.ok) {
//     throw new Error(`Failed to fetch mappings for ${controlId}`);
//   }

//   return response.json();
// }