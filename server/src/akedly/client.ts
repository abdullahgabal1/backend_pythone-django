/**
 * Akedly V1.2 REST API client (Shield).
 *
 * This module is the entire "connection to Akedly" — every other file in
 * this service is either validation, HTTP routing, or wiring. Nothing here
 * knows about Express; it can be dropped into any Node backend as-is.
 *
 * Credentials (AKEDLY_API_KEY, AKEDLY_PIPELINE_ID) are read from
 * process.env only. They are NEVER hardcoded, and this module never sends
 * them anywhere except https://api.akedly.io.
 *
 * Docs: https://docs.akedly.io/authentication/v1-2
 */

import { AkedlyApiError } from './errors.js'
import type {
  ChallengeResponse,
  SendOtpParams,
  SendOtpResponse,
  VerifyOtpParams,
  VerifyOtpResponse,
} from './types.js'

const BASE_URL = 'https://api.akedly.io/api/v1.2'
const DEFAULT_TIMEOUT_MS = 10_000

function getCredentials(): { apiKey: string; pipelineId: string } {
  const apiKey = process.env.AKEDLY_API_KEY
  const pipelineId = process.env.AKEDLY_PIPELINE_ID
  if (!apiKey || !pipelineId) {
    // Fail loud and immediately — this should never be reachable in
    // production if the server's startup env check (see server.ts) ran.
    throw new Error(
      'AKEDLY_API_KEY and AKEDLY_PIPELINE_ID must be set as environment variables. ' +
        'See server/.env.example. Never hardcode these values in source.',
    )
  }
  return { apiKey, pipelineId }
}

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs = DEFAULT_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await fetch(url, { ...init, signal: controller.signal })
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw new AkedlyApiError('Request to Akedly timed out.', {
        status: 504,
        code: 'CLIENT_TIMEOUT',
        retryable: true,
      })
    }
    throw new AkedlyApiError('Network error contacting Akedly.', {
      status: 502,
      code: 'NETWORK_ERROR',
      retryable: true,
    })
  } finally {
    clearTimeout(timer)
  }
}

/** Parses Akedly's { status, data, message } / { status, code, ... } envelope. */
async function parseAkedlyResponse<T>(res: Response): Promise<T> {
  let body: any
  try {
    body = await res.json()
  } catch {
    throw new AkedlyApiError('Akedly returned a non-JSON response.', {
      status: res.status,
      code: 'INVALID_RESPONSE',
      retryable: res.status >= 500,
    })
  }

  if (body?.status !== 'success') {
    throw new AkedlyApiError(body?.message ?? 'Akedly request failed.', {
      status: res.status,
      code: body?.code ?? 'UNKNOWN_ERROR',
      retryable: Boolean(body?.retryable),
      retryAfter: body?.retryAfter,
      cooldownSeconds: body?.cooldownSeconds,
      details: body?.details,
    })
  }

  return body.data as T
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Step 1 — GET a Proof-of-Work challenge + Turnstile config.
 *
 * This is a plain, idempotent GET, so it's the one call in this module
 * safe to retry automatically on transient failures.
 */
export async function getChallenge(): Promise<ChallengeResponse> {
  const { apiKey, pipelineId } = getCredentials()
  const url =
    `${BASE_URL}/transactions/challenge` +
    `?APIKey=${encodeURIComponent(apiKey)}&pipelineID=${encodeURIComponent(pipelineId)}`

  const maxAttempts = 3
  let lastErr: unknown
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      const res = await fetchWithTimeout(url, { method: 'GET' })
      return await parseAkedlyResponse<ChallengeResponse>(res)
    } catch (err) {
      lastErr = err
      const retryable = err instanceof AkedlyApiError ? err.retryable : true
      if (!retryable || attempt === maxAttempts - 1) break
      await sleep(200 * 2 ** attempt) // 200ms, 400ms
    }
  }
  throw lastErr
}

/**
 * Step 2 — Send the OTP.
 *
 * Deliberately NOT auto-retried: this call has a real-world side effect
 * (a WhatsApp/SMS/Telegram/email message may go out and get billed), and
 * Akedly only allows 1 resend per transaction. Blindly retrying here could
 * burn that resend or double-send. Instead this throws a structured
 * AkedlyApiError (with `.retryable` / `.retryAfter` / `.cooldownSeconds`)
 * so the caller — the route handler, then the frontend — can decide,
 * typically by surfacing a "resend in Ns" state to the user.
 *
 * @param endUserIp Pass the real end-user IP (see routes/otpRoutes.ts) to
 *   enable Akedly's per-IP rate-limit dimension. Omit it and Akedly simply
 *   skips that check rather than misattributing it to your server's IP.
 */
export async function sendOtp(
  params: SendOtpParams,
  endUserIp?: string,
): Promise<SendOtpResponse> {
  const { apiKey, pipelineId } = getCredentials()

  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (endUserIp) headers['x-end-user-ip'] = endUserIp

  const res = await fetchWithTimeout(`${BASE_URL}/transactions/send`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      APIKey: apiKey,
      pipelineID: pipelineId,
      verificationAddress: params.verificationAddress,
      powSolution: params.powSolution,
      turnstileToken: params.turnstileToken,
      ...(params.digits ? { digits: params.digits } : {}),
    }),
  })

  return parseAkedlyResponse<SendOtpResponse>(res)
}

/**
 * Step 3 — Verify the code the user typed in.
 *
 * Also not auto-retried: each wrong attempt counts toward Akedly's
 * server-side 10-attempt cap (MAX_ATTEMPTS_EXCEEDED force-expires the
 * transaction), so silently retrying on the client's behalf would burn
 * through that budget without the user knowing.
 */
export async function verifyOtp(params: VerifyOtpParams): Promise<VerifyOtpResponse> {
  const res = await fetchWithTimeout(`${BASE_URL}/transactions/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })

  return parseAkedlyResponse<VerifyOtpResponse>(res)
}
