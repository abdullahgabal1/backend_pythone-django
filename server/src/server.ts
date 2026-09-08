import 'dotenv/config'
import express from 'express'
import cors from 'cors'
import otpRoutes from './routes/otpRoutes.js'

// Fail fast at startup rather than on the first real request.
for (const key of ['AKEDLY_API_KEY', 'AKEDLY_PIPELINE_ID']) {
  if (!process.env[key]) {
    console.error(
      `Missing required environment variable: ${key}. ` +
        'Copy server/.env.example to server/.env and fill in your Akedly credentials ' +
        '(from https://app.akedly.io) — never hardcode them in source.',
    )
    process.exit(1)
  }
}

const app = express()

// Required so req.ip below reflects the real end-user IP rather than your
// reverse proxy/load balancer's IP — see otpRoutes.ts's use of req.ip.
app.set('trust proxy', 1)

app.use(
  cors({
    origin: process.env.ALLOWED_ORIGIN ? process.env.ALLOWED_ORIGIN.split(',') : true,
  }),
)
app.use(express.json())

app.get('/health', (_req, res) => res.json({ ok: true }))
app.use('/auth/akedly', otpRoutes)

const port = Number(process.env.PORT ?? 4000)
app.listen(port, () => {
  console.log(`Akedly OTP backend listening on http://localhost:${port}`)
})
