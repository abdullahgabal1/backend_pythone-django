// Egyptian mobile numbers in E.164: +20 1[0125] XXXXXXXX
const EGYPT_E164_RE = /^\+201[0125]\d{8}$/

/** Accepts local (01XXXXXXXXX) or already-E.164 (+201XXXXXXXXX) input and
 * normalizes to E.164, which is what Akedly's verificationAddress.phoneNumber
 * expects. */
export function normalizePhone(rawPhone: string): string {
  const trimmed = rawPhone.trim().replace(/[\s-]/g, '')
  if (trimmed.startsWith('+20')) return trimmed
  if (trimmed.startsWith('20')) return `+${trimmed}`
  if (trimmed.startsWith('0')) return `+20${trimmed.slice(1)}`
  return trimmed
}

export function isValidEgyptianPhone(rawPhone: unknown): rawPhone is string {
  if (typeof rawPhone !== 'string' || rawPhone.length === 0) return false
  return EGYPT_E164_RE.test(normalizePhone(rawPhone))
}
