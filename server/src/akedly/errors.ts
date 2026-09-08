export interface AkedlyErrorOptions {
  status: number
  code: string
  retryable?: boolean
  /** ISO timestamp — present on 429s. */
  retryAfter?: string
  cooldownSeconds?: number
  details?: unknown
}

/**
 * Wraps every non-"success" response from Akedly's API into a single,
 * predictable error shape so callers never have to parse Akedly's raw
 * JSON error body themselves.
 *
 * See the full error reference: https://docs.akedly.io/authentication/v1-2#error-reference
 */
export class AkedlyApiError extends Error {
  readonly status: number
  readonly code: string
  readonly retryable: boolean
  readonly retryAfter?: string
  readonly cooldownSeconds?: number
  readonly details?: unknown

  constructor(message: string, opts: AkedlyErrorOptions) {
    super(message)
    this.name = 'AkedlyApiError'
    this.status = opts.status
    this.code = opts.code
    this.retryable = opts.retryable ?? false
    this.retryAfter = opts.retryAfter
    this.cooldownSeconds = opts.cooldownSeconds
    this.details = opts.details
  }
}
