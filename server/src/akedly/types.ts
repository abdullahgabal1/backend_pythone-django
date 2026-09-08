// Types for the Akedly V1.2 REST API (Shield).
// Reference: https://docs.akedly.io/authentication/v1-2

export interface ChallengeResponse {
  challenge: string
  difficulty: number
  challengeToken: string
  challengeRequired: boolean
  turnstile: {
    required: boolean
    siteKey?: string
  }
}

export interface PowSolution {
  challengeToken: string
  nonce: number
}

export interface SendOtpParams {
  verificationAddress: {
    phoneNumber: string
    email?: string
  }
  powSolution: PowSolution
  turnstileToken?: string
  /** Optional. 4, 5 or 6. Defaults to 6 on Akedly's side if omitted/out of range. */
  digits?: 4 | 5 | 6
}

export interface SendOtpResponse {
  transactionID: string
  /** Save this — required for the verify step. */
  transactionReqID: string
  channels: Array<'whatsapp' | 'telegram' | 'sms' | 'email'>
  /** ISO 8601 timestamp. */
  expiresAt: string
}

export interface VerifyOtpParams {
  transactionReqID: string
  otp: string
  returnTarget?: { origin?: string; url?: string }
}

export interface VerifyOtpResponse {
  verified: boolean
  transactionID: string
  frontendCallbackURL?: string
  /** Only present when passkeys are enabled for both account and pipeline. */
  enrollmentToken?: string
}
