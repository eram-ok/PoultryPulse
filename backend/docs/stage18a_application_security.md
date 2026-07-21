# Stage 18A — Application Security Hardening

Stage 18A adds dependency-free security controls to the PoultryPulse API.

## Controls

- production-only validation of debug mode, JWT secret strength, trusted
  hosts, token issuer/audience validation and authentication throttling;
- trusted-host enforcement;
- explicit CORS allowlists;
- security response headers;
- authentication response cache prevention;
- request-body size limits;
- IP-based authentication throttling;
- trusted-proxy-aware client IP handling;
- JWT issuer and audience claims;
- configurable issuer and audience validation;
- generic 500 responses without internal error details;
- optional API documentation exposure;
- environment and generated-artifact ignore rules.

## Compatibility

Development defaults remain permissive enough for the existing test suite:

- `testserver` is an allowed host;
- authentication rate limiting is disabled;
- issuer/audience enforcement is disabled;
- HSTS is disabled;
- API documentation is enabled.

Production startup is deliberately stricter and requires explicit secure
environment values.

## Deployment note

When `JWT_VALIDATE_ISSUER_AUDIENCE=true`, refresh tokens issued before Stage
18A may no longer validate because older tokens do not contain issuer and
audience claims. Users should sign in again after production deployment.

## No migration

Stage 18A does not alter the database schema.
