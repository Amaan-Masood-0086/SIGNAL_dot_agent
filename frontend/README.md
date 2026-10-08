# SIGNAL frontend

Next.js 16 / React 19 workspace for institution caretakers and system administrators.
See the [UI redesign notes](../docs/technical/SIGNAL_UI_Redesign_2026-09-11.md) for the updated screens, role boundaries and remaining product work.

## Verification

```powershell
npm.cmd run lint
npm.cmd run test
npm.cmd run build
npm.cmd run test:ui
```

Browser tests use installed Chrome and an isolated synthetic fixture API. They start their own servers on ports 3015 and 18119, without connecting to the configured real backend or making paid provider calls. Screenshots are generated in `test-results/`.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

The interface uses Bricolage Grotesque and Noto Sans through `next/font`. Configure `BACKEND_URL` using `.env.example` before signing in to the normal application.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
