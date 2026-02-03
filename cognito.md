# Cognito Configuration

## User Pool

| Key              | Value                                                                          |
| ---------------- | ------------------------------------------------------------------------------ |
| Pool Name        | running-corgium                                                                |
| Pool ID          | us-east-2_FbR5oGK5X                                                           |
| ARN              | arn:aws:cognito-idp:us-east-2:170744924235:userpool/us-east-2_FbR5oGK5X       |
| Region           | us-east-2                                                                      |
| Username         | email                                                                          |
| Auto-verify      | email                                                                          |
| MFA              | OFF                                                                            |
| Password policy  | min 8, uppercase, lowercase, numbers required; symbols not required            |

## App Client

| Key              | Value                                                                          |
| ---------------- | ------------------------------------------------------------------------------ |
| Client Name      | running-corgium-web                                                            |
| Client ID        | 5a7mim2os4br7vg4ikv2tejsr                                                      |
| Client Secret    | none (public client)                                                           |
| Auth Flows       | ALLOW_USER_SRP_AUTH, ALLOW_REFRESH_TOKEN_AUTH                                  |
| OAuth Flows      | authorization code                                                             |
| OAuth Scopes     | openid, email                                                                  |
| Callback URL     | https://5en3exrtx6.execute-api.us-east-2.amazonaws.com/auth/callback           |
| Logout URL       | https://5en3exrtx6.execute-api.us-east-2.amazonaws.com/                        |

## Hosted UI Domain

| Key              | Value                                                                          |
| ---------------- | ------------------------------------------------------------------------------ |
| Domain prefix    | running-corgium                                                                |
| Full domain      | running-corgium.auth.us-east-2.amazoncognito.com                               |

## API Gateway JWT Authorizer

| Key              | Value                                                                          |
| ---------------- | ------------------------------------------------------------------------------ |
| Authorizer ID    | sz5uco                                                                         |
| Type             | JWT                                                                            |
| Identity Source  | $request.header.Authorization                                                  |
| Issuer           | https://cognito-idp.us-east-2.amazonaws.com/us-east-2_FbR5oGK5X               |
| Audience         | 5a7mim2os4br7vg4ikv2tejsr                                                      |

### Protected Routes

| Route Key              | Route ID  |
| ---------------------- | --------- |
| GET /users/me          | zcjx35l   |
| GET /strava/athlete    | 7xtxok1   |
| GET /strava/activities | 6a8jneo   |
The `$default` route (d3xmuae) has NO authorizer — serves the SPA, static assets, `/auth/callback`, and `/strava/authorize` (OAuth callback).

## Frontend Environment Variables

```
VITE_AUTH_MODE=cognito
VITE_COGNITO_DOMAIN=running-corgium.auth.us-east-2.amazoncognito.com
VITE_COGNITO_CLIENT_ID=5a7mim2os4br7vg4ikv2tejsr
VITE_COGNITO_REDIRECT_URI=https://5en3exrtx6.execute-api.us-east-2.amazonaws.com/auth/callback
```

## Deployment Notes

### Issue: 405 after first deploy (2026-02-02)

**Symptom:** After deploying the Cognito-enabled image, the SPA still returned 405 on login.

**Root cause:** The frontend JS bundle baked into the Docker image had `authMode:"standalone"` instead of `authMode:"cognito"`. Vite inlines `VITE_*` env vars at build time — if they're missing, the fallback `'standalone'` is used, which makes the SPA POST to `/auth/jwt/login` (a route that doesn't exist in AWS/dynamodb mode, hence 405).

**What went wrong:** The `bun run build` with `VITE_AUTH_MODE=cognito` produced `index-CUd7NqQT.js` (correct), but `docker build` picked up a stale `frontend/dist/` containing `index-DzzNigWo.js` (standalone). Docker BuildKit can snapshot the build context before all host-side changes are flushed, especially on macOS.

**Fix:** Rebuilt with `docker build --no-cache` immediately after `bun run build`, then verified the bundle:

```bash
# 1. Build frontend with VITE_ env vars
cd frontend
VITE_AUTH_MODE=cognito \
VITE_COGNITO_DOMAIN=running-corgium.auth.us-east-2.amazoncognito.com \
VITE_COGNITO_CLIENT_ID=5a7mim2os4br7vg4ikv2tejsr \
VITE_COGNITO_REDIRECT_URI=https://5en3exrtx6.execute-api.us-east-2.amazonaws.com/auth/callback \
bun run build

# 2. Verify the bundle has cognito config
grep -o 'authMode:"[^"]*"' dist/assets/index-*.js
# Expected: authMode:"cognito"

# 3. Docker build with --no-cache
cd ..
docker build --platform linux/amd64 --provenance=false --no-cache \
  -f Dockerfile.lambda -t running-corgium:latest .

# 4. Tag, push, update Lambda
docker tag running-corgium:latest 170744924235.dkr.ecr.us-east-2.amazonaws.com/running-corgium:latest
docker push 170744924235.dkr.ecr.us-east-2.amazonaws.com/running-corgium:latest
aws lambda update-function-code --function-name running-corgium \
  --image-uri 170744924235.dkr.ecr.us-east-2.amazonaws.com/running-corgium:latest --region us-east-2
```

**Prevention:** Always verify `authMode` in the built JS bundle before running `docker build`. The grep check in step 2 above catches mismatches before they reach production.

### Issue: Cognito redirect error — invalid scope (2026-02-02)

**Symptom:** Clicking "Sign in" redirected to Cognito, which immediately returned a 302 error.

**Root cause:** `cognito.ts` requested `scope: 'openid email profile'` but the App Client only allows `openid` and `email`. The `profile` scope was not in the allowed list, so Cognito rejected the request.

**Fix:** Changed `cognito.ts` scope to `'openid email'`.

### Issue: Strava redirect_uri invalid (2026-02-02)

**Symptom:** After Cognito login, clicking the Strava login link returned `{"message":"Bad Request","errors":[{"resource":"Application","field":"redirect_uri","code":"invalid"}]}`.

**Root cause — three overlapping problems:**

1. **Wrong default URI:** `config.py` had `strava_redirect_uri` defaulting to `/auth/callback` (the Cognito callback route). The actual Strava callback handler is `/strava/authorize`.

2. **URI not registered with Strava:** The API Gateway URL wasn't registered as an authorized redirect URI in the Strava app settings (strava.com/settings/api).

3. **JWT authorizer blocked the callback:** We had attached the API Gateway JWT authorizer to `GET /strava/authorize`. Strava's browser redirect back to this URL doesn't include a JWT token, so API Gateway would reject it with 401 before the Lambda even sees the request.

**Fixes applied:**

- Reverted `strava_redirect_uri` default in `config.py` to `http://localhost:8000/strava/authorize` (local dev).
- Added `STRAVA_REDIRECT_URI=https://5en3exrtx6.execute-api.us-east-2.amazonaws.com/strava/authorize` to Secrets Manager (Lambda picks this up at runtime).
- Deleted the `GET /strava/authorize` protected route (f1rjr4k) from API Gateway. The request now falls through to `$default` (no authorizer), which is correct for an OAuth callback.

**Still required:** Register `https://5en3exrtx6.execute-api.us-east-2.amazonaws.com/strava/authorize` as an authorized "Authorization Callback Domain" in your Strava API app settings at https://www.strava.com/settings/api. The domain to enter is: `5en3exrtx6.execute-api.us-east-2.amazonaws.com`.

### Issue: Strava login loop — session cookie lost during OAuth redirect (2026-02-02)

**Symptom:** Strava OAuth completed successfully but the dashboard never loaded Strava data. Connecting Strava kept returning to "Connect Strava" in a loop.

**Root cause:** The `session_id` cookie was set with `samesite="strict"`. When Strava redirected back to `/strava/authorize`, the browser treated it as a cross-site navigation (originating from strava.com) and did **not** send the cookie. The backend received `session_id=None`, so Strava tokens were stored against a `None` key. On subsequent same-site API calls from the dashboard, the cookie was sent with its real value, but no tokens existed for that key — resulting in 401.

**Fix:** Changed `samesite="strict"` to `samesite="lax"` in the session cookie. With `lax`, the cookie is sent on top-level GET navigations from third-party sites, which is exactly what an OAuth redirect is.

### Issue: /strava/authorize returned JSON instead of redirecting (2026-02-02)

**Symptom:** After Strava OAuth, the browser showed raw JSON `{"message":"<code>"}` instead of the dashboard.

**Root cause:** The `/strava/authorize` endpoint returned `{"message": code}` — appropriate for an API client but not for a browser redirect flow.

**Fix:** Changed the success response from `return {"message": code}` to `return RedirectResponse(url="/dashboard")`.

---

## Transition Challenges: fastapi-users to Cognito

### Summary

Migrating from fastapi-users (standalone, self-contained auth) to AWS Cognito (managed, external auth) touched nearly every layer of the stack. The core difficulty is that fastapi-users owns the entire auth lifecycle within the app, while Cognito pushes auth to the infrastructure boundary — API Gateway validates tokens before Lambda sees the request, and the user database lives outside the application.

### 1. Two auth models, one codebase

fastapi-users handles login, registration, token issuance, and user storage inside the FastAPI app. Cognito moves all of this outside: the Hosted UI handles login/signup, API Gateway validates JWTs, and user data lives in the User Pool. The codebase now has conditional code paths (`if settings.db_backend == "standalone"` vs `else`) for route registration, auth dependencies, and user resolution. Every auth-related route, middleware, and dependency had to be duplicated or made conditional.

### 2. Frontend must switch auth flows at build time

With fastapi-users, the frontend POSTs credentials to `/auth/jwt/login` and gets a JWT back. With Cognito, there's no login endpoint on the backend — the frontend redirects to the Cognito Hosted UI and exchanges an authorization code for tokens client-side. This required:
- A `VITE_AUTH_MODE` env var to switch behavior at build time (Vite inlines it)
- A completely separate `cognito.ts` API module for Hosted UI URL construction and token exchange
- Dual-mode logic in `AuthContext` (token validation via `/users/me` vs local JWT expiry check)
- Dual-mode `OAuthCallback` (Strava code exchange vs Cognito code exchange)
- The built JS bundle bakes in the auth mode — you can't switch at runtime. A standalone build hitting a Cognito backend (or vice versa) breaks silently with 405 errors.

### 3. API Gateway authorizer vs application-level auth

fastapi-users validates tokens inside the app using `Depends(current_active_user)`. Cognito shifts validation to API Gateway's JWT authorizer, which runs before the Lambda is invoked. This has consequences:
- **401s are invisible to the app:** If the JWT is invalid or missing, API Gateway returns 401 and the Lambda never executes. No CloudWatch logs, no application-level error handling.
- **OAuth callbacks break:** Strava's redirect to `/strava/authorize` doesn't carry a JWT. Attaching a JWT authorizer to that route blocked the callback entirely. OAuth callback routes must be excluded from the authorizer.
- **Route-level granularity required:** Instead of a single `$default` route, you need explicit protected routes (with authorizer) and unprotected routes (SPA, static assets, OAuth callbacks) falling through to `$default`.

### 4. Cookie behavior changes across deployment contexts

The `session_id` cookie (used to associate Strava OAuth tokens with a browser session) worked fine in standalone mode where everything is same-origin. In the Lambda context:
- `samesite="strict"` broke the Strava OAuth flow because the redirect from strava.com was treated as cross-site, dropping the cookie.
- Had to relax to `samesite="lax"` to allow the cookie on top-level GET redirects from third parties.
- Cookies travel a longer path: browser → API Gateway → Lambda (via Mangum). Any misconfiguration in this chain silently drops them.

### 5. Configuration splits across multiple systems

With fastapi-users, all config lives in `.env` / environment variables. With Cognito, configuration is spread across:
- **AWS Secrets Manager:** Backend secrets (Strava creds, DB config, redirect URIs)
- **Cognito User Pool:** Password policy, verified attributes, App Client settings
- **API Gateway:** JWT authorizer config, route-level auth assignments
- **Vite build-time env vars:** `VITE_AUTH_MODE`, `VITE_COGNITO_DOMAIN`, `VITE_COGNITO_CLIENT_ID`, `VITE_COGNITO_REDIRECT_URI`
- **Strava app settings:** Authorized redirect domains

A single misconfigured value (wrong scope, wrong redirect URI, missing secret) produces opaque errors. Debugging requires checking multiple AWS consoles.

### 6. Two callback URLs, one route

The app now has two OAuth flows using different callback paths:
- **Cognito callback:** `/auth/callback` — handled client-side by the SPA's `OAuthCallback` component
- **Strava callback:** `/strava/authorize` — handled server-side by the FastAPI endpoint

In standalone mode, Strava used `/auth/callback` (SPA route). In AWS mode, Strava must use `/strava/authorize` (backend route) because the SPA's `OAuthCallback` component checks `authMode` and would try to exchange the Strava code with Cognito's token endpoint.

### 7. No `/users/me` in AWS mode

fastapi-users provides `GET /users/me` automatically. In Cognito mode, this route doesn't exist — user info comes from JWT claims in the API Gateway event context. A stub endpoint had to be added in the `else` block to return user info extracted from Cognito claims, so the frontend's token validation flow works in both modes.