/** Avalanche USDC / EURC use 6 decimals. */
export const PAYMENT_DECIMALS = 6;

export function formatAtomic(amount: number | bigint, decimals = PAYMENT_DECIMALS): string {
  const value = BigInt(amount);
  const base = 10n ** BigInt(decimals);
  const whole = value / base;
  const frac = (value % base).toString().padStart(decimals, "0").replace(/0+$/, "");
  return frac ? `${whole}.${frac}` : whole.toString();
}

export function shortAddress(address: string | null | undefined): string {
  if (!address) return "—";
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

export const CHAIN_NAMES: Record<number, string> = {
  43113: "Avalanche Fuji",
  43114: "Avalanche C-Chain",
};
