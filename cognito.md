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
| GET /strava/authorize  | f1rjr4k   |

The `$default` route (d3xmuae) has NO authorizer — serves the SPA, static assets, and `/auth/callback`.

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