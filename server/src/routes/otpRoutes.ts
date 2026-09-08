import { Router, type Request, type Response } from 'express'
import rateLimit from 'express-rate-limit'
import { getChallenge, sendOtp, verifyOtp } from '../akedly/client.js'
import { AkedlyApiError } from '../akedly/errors.js'
import { isValidEgyptianPhone, normalizePhone } from '../validators/phone.js'

const router = Router()

// Defense-in-depth on top of Akedly's own per-phone/per-pipeline/per-IP
// rate limits (which apply regardless). This is an in-memory limiter —
// fine for a single instance; switch to a shared store (e.g.
// rate-limit-redis) before running more than one backend process, or this
// limit resets per-instance and stops being meaningful.
const otpLimiter = rateLimit({
  windowMs: 60_000,
  limit: 10,
  standardHeaders: true,
  legacyHeaders: false,
})
router.use(otpLimiter)

function sendErrorResponse(res: Response, err: unknown): void {
  if (err instanceof AkedlyApiError) {
    res.status(err.status || 502).json({
      success: false,
      message: err.message,
      errors: [
        {
          code: err.code,
          retryable: err.retryable,
          retryAfter: err.retryAfter,
          cooldownSeconds: err.cooldownSeconds,
        },
      ],
    })
    return
  }
  console.error('Unexpected error in OTP route:', err)
  res.status(500).json({ success: false, message: 'Internal server error.', errors: null })
}

/**
 * Step 1 — GET a Proof-of-Work challenge + Turnstile site key for the
 * frontend to solve via @akedly/shield.
 */
router.get('/challenge', async (_req: Request, res: Response) => {
  try {
    const data = await getChallenge()
    res.json({ success: true, data })
  } catch (err) {
    sendErrorResponse(res, err)
  }
})

/**
 * Step 2 — Send the OTP once the client has solved the challenge.
 * Server-side validation happens here — never trust the frontend's own
 * phone-format checks, since a client can call this endpoint directly.
 */
router.post('/send', async (req: Request, res: Response) => {
  const { phoneNumber, powSolution, turnstileToken, digits } = req.body ?? {}

  if (!isValidEgyptianPhone(phoneNumber)) {
    res.status(400).json({
      success: false,
      message: 'A valid Egyptian phone number is required.',
      errors: [{ field: 'phoneNumber', code: 'invalid_format' }],
    })
    return
  }

  if (!powSolution?.challengeToken || typeof powSolution?.nonce !== 'number') {
    res.status(400).json({
      success: false,
      message: 'Missing or malformed proof-of-work solution.',
      errors: [{ field: 'powSolution', code: 'required' }],
    })
    return
  }

  if (digits !== undefined && ![4, 5, 6].includes(digits)) {
    res.status(400).json({
      success: false,
      message: 'digits must be 4, 5, or 6 if provided.',
      errors: [{ field: 'digits', code: 'invalid_value' }],
    })
    return
  }

  try {
    const data = await sendOtp(
      {
        verificationAddress: { phoneNumber: normalizePhone(String(phoneNumber)) },
        powSolution,
        turnstileToken,
        digits,
      },
      req.ip, // real end-user IP — see app.set('trust proxy', 1) in server.ts
    )
    res.json({ success: true, data })
  } catch (err) {
    sendErrorResponse(res, err)
  }
})

/**
 * Step 3 — Verify the code the user typed in.
 */
router.post('/verify', async (req: Request, res: Response) => {
  const { transactionReqID, otp } = req.body ?? {}

  if (typeof transactionReqID !== 'string' || transactionReqID.length === 0) {
    res.status(400).json({
      success: false,
      message: 'transactionReqID is required.',
      errors: [{ field: 'transactionReqID', code: 'required' }],
    })
    return
  }

  if (typeof otp !== 'string' || !/^\d{4,6}$/.test(otp)) {
    res.status(400).json({
      success: false,
      message: 'A valid 4-6 digit numeric OTP code is required.',
      errors: [{ field: 'otp', code: 'invalid_format' }],
    })
    return
  }

  try {
    const data = await verifyOtp({ transactionReqID, otp })
    res.json({ success: true, data })
  } catch (err) {
    sendErrorResponse(res, err)
  }
})

export default router
