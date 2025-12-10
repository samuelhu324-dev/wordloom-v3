export const DEFAULT_LIBRARY_SILVER_GRADIENT =
  'linear-gradient(135deg, #f8fafc 0%, #e4e7ee 45%, #ccd1dc 70%, #b5bac6 100%)';

export function coverGradientFromId(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  }
  const hue1 = hash % 360;
  const hue2 = (hash >> 5) % 360;
  return `linear-gradient(135deg, hsl(${hue1} 60% 80%), hsl(${hue2} 55% 70%))`;
}
