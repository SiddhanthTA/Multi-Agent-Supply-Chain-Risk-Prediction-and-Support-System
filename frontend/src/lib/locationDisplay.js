export function isUnknownLocation(value) {
  if (value === null || value === undefined) return true;
  return String(value).trim().toLowerCase() === 'unknown';
}

export function formatLocationDisplay(value) {
  if (isUnknownLocation(value)) {
    return {
      label: 'Global',
      secondary: 'No specific location identified',
      isUnknown: true,
    };
  }

  return {
    label: String(value).trim(),
    secondary: null,
    isUnknown: false,
  };
}
