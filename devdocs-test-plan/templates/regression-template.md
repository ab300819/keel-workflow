# Pre-release Regression Template

Use this template to generate `docs/prd/03-test-regression.md`.

```markdown
# Pre-release Regression Plan: <Feature Name>

## Regression Checklist

| # | Check Item | Method | Pass Criteria | Owner |
|---|------------|--------|---------------|-------|
| 1 | Code merge | Manual | PR merged, no conflicts | Dev |
| 2 | Unit tests | CI Auto | All pass, coverage >= 80% | Dev |
| 3 | UI automation | CI Auto | All P0 cases pass | QA |
| 4 | Core function verification | Manual | All P0 cases pass | QA |
| 5 | Compatibility check | Manual | No issues on major browsers | QA |
| 6 | Performance check | Auto/Manual | Meets performance targets | Dev |
| 7 | Security scan | Auto | No high/critical vulnerabilities | Dev |
| 8 | Code review | Manual | Approved by reviewer | Dev |

## Execution Flow

```
1. Code Freeze
   │
   ▼
2. Create Release Branch
   │
   ▼
3. Run CI Pipeline
   ├── Unit Tests
   ├── UI Automation
   └── Security Scan
   │
   ▼
4. [If Failed] Fix and Re-run
   │
   ▼
5. Deploy to Staging
   │
   ▼
6. Execute P0 Manual Tests
   │
   ▼
7. Execute Compatibility Tests
   │
   ▼
8. Performance Verification
   │
   ▼
9. Product Sign-off
   │
   ▼
10. Release Approval
    │
    ▼
11. Production Deployment
    │
    ▼
12. Production Smoke Test
    │
    ▼
13. Monitor (24h)
```

## Environment Checklist

### Pre-deployment

- [ ] Staging environment matches production config
- [ ] Database migrations tested
- [ ] Feature flags configured
- [ ] Rollback scripts prepared
- [ ] Monitoring alerts configured

### Deployment

- [ ] Deployment window scheduled
- [ ] On-call engineers notified
- [ ] Stakeholders informed
- [ ] Runbook reviewed

## Rollback Conditions

| Severity | Trigger Condition | Rollback Strategy | Decision Time |
|----------|-------------------|-------------------|---------------|
| P0 | Core function unavailable | Immediate rollback | < 5 min |
| P1 | Major UX impact | Evaluate and decide | < 30 min |
| P2 | Minor issues | Hotfix in next release | N/A |

### Rollback Procedure

```bash
# 1. Confirm rollback decision
# 2. Execute rollback
./scripts/rollback.sh <previous-version>

# 3. Verify rollback
./scripts/smoke-test.sh

# 4. Notify stakeholders
./scripts/notify.sh --event rollback --version <version>
```

## Post-release Verification

### Immediate (0-30 min)

- [ ] Smoke test pass
- [ ] No error spike in logs
- [ ] Key metrics normal (latency, error rate)
- [ ] User-facing features accessible

### Short-term (30 min - 2 hours)

- [ ] Business metrics normal
- [ ] No increase in support tickets
- [ ] Performance metrics stable
- [ ] Third-party integrations working

### Extended (2-24 hours)

- [ ] No memory leaks
- [ ] Database performance stable
- [ ] Async jobs completing normally
- [ ] User feedback monitored

## Monitoring Dashboard

| Metric | Normal Range | Alert Threshold | Dashboard Link |
|--------|--------------|-----------------|----------------|
| Error rate | < 0.1% | > 1% | [Link] |
| P99 latency | < 500ms | > 2s | [Link] |
| CPU usage | < 60% | > 80% | [Link] |
| Memory usage | < 70% | > 85% | [Link] |

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Dev Lead | | | |
| QA Lead | | | |
| Product Owner | | | |
| Ops | | | |
```

## Notes

- Update checklist items based on project-specific requirements
- Adjust rollback decision times based on business criticality
- Ensure monitoring dashboards are set up before release
