# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of this project seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do NOT Create a Public Issue

Security vulnerabilities should not be reported through public GitHub issues.

### 2. Report Privately

Send a detailed report to: **security@example.com** (or use GitHub's private vulnerability reporting)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: 24-48 hours
  - High: 7 days
  - Medium: 30 days
  - Low: 90 days

### 4. Disclosure Policy

- We will acknowledge receipt of your report
- We will investigate and validate the issue
- We will develop and test a fix
- We will release the fix and publicly disclose the vulnerability
- We will credit you (unless you prefer to remain anonymous)

## Security Measures

### Application Security

- **Input Validation**: All inputs are validated using Pydantic models
- **SQL Injection**: N/A (no SQL database in this demo)
- **XSS Prevention**: FastAPI's automatic response encoding
- **CORS**: Configurable CORS policies
- **Rate Limiting**: Recommended for production

### Infrastructure Security

- **Non-root Containers**: Application runs as non-root user
- **Secrets Management**: Environment variables, not hardcoded
- **Network Isolation**: Docker networks for service isolation
- **TLS**: Recommended for production (handled by reverse proxy)

### CI/CD Security

- **SAST**: Bandit for Python security scanning
- **Dependency Scanning**: Safety and pip-audit
- **Container Scanning**: Trivy for vulnerability detection
- **Secret Detection**: Gitleaks for secret scanning
- **CodeQL**: GitHub's code scanning

### Dependency Management

- **Pinned Versions**: All dependencies have pinned versions
- **Dependabot**: Automated security updates
- **Regular Audits**: Weekly security scans

## Security Best Practices

### For Developers

1. **Never commit secrets** to the repository
2. **Use environment variables** for sensitive configuration
3. **Keep dependencies updated** - run `make security` regularly
4. **Review code** for security issues before merging
5. **Use pre-commit hooks** to catch issues early

### For Deployers

1. **Use HTTPS** in production
2. **Configure proper CORS** origins
3. **Set up rate limiting**
4. **Use secrets management** (Vault, AWS Secrets Manager, etc.)
5. **Enable audit logging**
6. **Regular security updates**
7. **Network segmentation**
8. **Principle of least privilege**

### Production Checklist

- [ ] HTTPS enabled
- [ ] Debug mode disabled
- [ ] Proper CORS configuration
- [ ] Rate limiting enabled
- [ ] Secrets in secure storage
- [ ] Non-root container user
- [ ] Network policies configured
- [ ] Logging enabled
- [ ] Monitoring alerts configured
- [ ] Backup and recovery tested

## Security Tools

### Running Security Checks

```bash
# Run all security checks
make security

# Individual tools
bandit -r app/           # SAST
safety check -r requirements.txt   # Dependency scan
```

### Pre-commit Hooks

Security checks are included in pre-commit hooks:
- Bandit for Python security
- Detect private keys
- Check for large files

## Known Security Considerations

### Demo Application Limitations

This is a demonstration project. For production use:

1. **Add Authentication**: Implement proper authentication (JWT, OAuth2)
2. **Add Authorization**: Role-based access control
3. **Enable Rate Limiting**: Prevent abuse
4. **Use Real Database**: With proper security configuration
5. **Enable Audit Logging**: Track all sensitive operations
6. **Configure WAF**: Web Application Firewall

### Current Security Features

- ✅ Input validation
- ✅ CORS configuration
- ✅ Health check endpoints
- ✅ Non-root containers
- ✅ Security scanning in CI
- ✅ Dependency updates
- ⚠️ No authentication (demo only)
- ⚠️ No rate limiting (demo only)
- ⚠️ In-memory storage (demo only)

## Contact

For security concerns: security@example.com

For general questions: Open a GitHub issue
