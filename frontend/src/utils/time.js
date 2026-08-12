/**
 * Converts a UTC time string (e.g., "19:29:57" or ISO timestamp) into the browser's local time string.
 * Works dynamically in any user timezone without hardcoded offsets.
 */
export function formatToLocalTime(timeInput) {
  if (!timeInput) return new Date().toLocaleTimeString();

  const strInput = String(timeInput).trim();

  // If timeInput is HH:MM:SS format (e.g. "19:29:57" from UTC backend), attach today's date in UTC
  if (/^\d{2}:\d{2}:\d{2}$/.test(strInput)) {
    const today = new Date().toISOString().split('T')[0];
    const dateObj = new Date(`${today}T${strInput}Z`);
    if (!isNaN(dateObj.getTime())) {
      return dateObj.toLocaleTimeString();
    }
  }

  // If timeInput is a full ISO timestamp string or numeric timestamp
  const dateObj = new Date(strInput);
  if (!isNaN(dateObj.getTime())) {
    return dateObj.toLocaleTimeString();
  }

  return strInput;
}
