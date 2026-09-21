/** Weather for the idle dashboard: the daemon has internet, the Pi never
 * needs a route out (docs/SAFETY.md rule 6). Uses open-meteo, no API key. */

const LAT = process.env.DECK_LAT;
const LON = process.env.DECK_LON;

const WEATHER_CODES: Record<number, string> = {
  0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
  45: "fog", 48: "fog", 51: "drizzle", 61: "rain", 63: "rain", 65: "heavy rain",
  71: "snow", 73: "snow", 75: "heavy snow", 80: "showers", 95: "storm",
};

export async function getWeather(): Promise<string | null> {
  if (!LAT || !LON) return null; // unset: don't guess the user's location
  try {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${LAT}&longitude=${LON}&current=temperature_2m,weather_code&temperature_unit=celsius`;
    const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) return null;
    const data = (await res.json()) as {
      current?: { temperature_2m?: number; weather_code?: number };
    };
    const temp = data.current?.temperature_2m;
    const code = data.current?.weather_code;
    if (temp === undefined) return null;
    const label = code !== undefined ? WEATHER_CODES[code] ?? "" : "";
    return `${Math.round(temp)}°C ${label}`.trim();
  } catch {
    return null; // no internet, DNS hiccup, whatever: the dashboard just omits it
  }
}
