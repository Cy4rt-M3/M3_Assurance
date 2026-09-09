/**
 * CyBreach Assurance Module - Data Export Utilities
 *
 * Provides browser-side CSV and JSON export with deterministic file naming,
 * RFC-4180-friendly CSV escaping, and toast-friendly return metadata.
 */

/**
 * Convert an array of objects to CSV format and trigger a browser download.
 *
 * @param data     Array of records to export.
 * @param filename Base filename (without extension).
 * @param headers  Optional ordered list of column keys. Defaults to the keys
 *                 of the first record. Keys not present on a record are
 *                 rendered as empty cells.
 */
export function exportToCSV(
  data: Record<string, unknown>[],
  filename: string,
  headers?: string[],
): { count: number; filename: string } | null {
  if (!data.length) return null;

  const keys = headers && headers.length ? headers : Object.keys(data[0]);

  const escapeCell = (value: unknown): string => {
    if (value === null || value === undefined) return '';
    if (typeof value === 'object') {
      // Flatten arrays/objects to a JSON string so they survive CSV round-trips.
      return JSON.stringify(value);
    }
    return String(value);
  };

  const csvContent = [
    keys.join(','),
    ...data.map((row) =>
      keys
        .map((key) => {
          const str = escapeCell(row[key]);
          // Escape quotes and wrap in quotes if it contains comma, quote, or newline
          if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
            return `"${str.replace(/"/g, '""')}"`;
          }
          return str;
        })
        .join(','),
    ),
  ].join('\n');

  // Prepend BOM so Excel reads UTF-8 correctly.
  const withBom = `\uFEFF${csvContent}`;
  downloadFile(withBom, `${filename}.csv`, 'text/csv;charset=utf-8;');

  return { count: data.length, filename: `${filename}.csv` };
}

/**
 * Export any JSON-serializable data as a `.json` file download.
 */
export function exportToJSON(
  data: unknown,
  filename: string,
): { filename: string } {
  const jsonContent = JSON.stringify(data, null, 2);
  downloadFile(jsonContent, `${filename}.json`, 'application/json');
  return { filename: `${filename}.json` };
}

/**
 * Trigger a file download in the browser by creating a temporary anchor
 * element and revoking the object URL afterwards.
 */
function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  // Defer revocation slightly so Safari/Firefox can complete the download.
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

/**
 * Format a timestamp for use in filenames (YYYY-MM-DD_HHMM).
 */
export function timestampForFilename(): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}`;
}

/**
 * Sanitize a free-form label (e.g. report title) for safe inclusion in a
 * filename. Replaces any non-alphanumeric character with `_`.
 */
export function sanitizeFilenameSegment(label: string): string {
  const trimmed = label.trim().replace(/[^a-zA-Z0-9-_]+/g, '_');
  return trimmed.length ? trimmed.slice(0, 60) : 'export';
}
