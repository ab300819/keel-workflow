# Manual Test Template

Use this template to generate `docs/prd/03-test-manual.md`.

```markdown
# Manual Test Cases: <Feature Name>

## Test Scope

Based on requirements document acceptance criteria AC-01 to AC-XX.

## 1. Positive Tests

Verify normal business flows work correctly.

| Case ID | Scenario | Preconditions | Steps | Expected Result | Priority |
|---------|----------|---------------|-------|-----------------|----------|
| TC-P-001 | <scenario> | - User logged in<br>- Valid data exists | 1. Navigate to page<br>2. Click button<br>3. Verify result | - Success message displayed<br>- Data saved correctly | P0 |
| TC-P-002 | <scenario> | <conditions> | 1. ...<br>2. ... | <expected> | P0 |

## 2. Negative Tests

Verify error handling and validation.

| Case ID | Scenario | Preconditions | Steps | Expected Result | Priority |
|---------|----------|---------------|-------|-----------------|----------|
| TC-N-001 | Invalid input | User on form page | 1. Leave required field empty<br>2. Click submit | - Error message "Field required"<br>- Form not submitted | P0 |
| TC-N-002 | Unauthorized access | User not logged in | 1. Access protected page directly | - Redirect to login<br>- Error message shown | P0 |
| TC-N-003 | Duplicate entry | Record exists | 1. Try to create duplicate | - Error "Already exists"<br>- No duplicate created | P1 |

## 3. Boundary Tests

Verify edge cases and limits.

| Case ID | Scenario | Preconditions | Steps | Expected Result | Priority |
|---------|----------|---------------|-------|-----------------|----------|
| TC-B-001 | Minimum value | - | 1. Enter minimum allowed value<br>2. Submit | - Accepted<br>- Processed correctly | P1 |
| TC-B-002 | Maximum value | - | 1. Enter maximum allowed value<br>2. Submit | - Accepted<br>- Processed correctly | P1 |
| TC-B-003 | Empty list | No data exists | 1. Load list page | - Empty state displayed<br>- "No data" message shown | P1 |
| TC-B-004 | Large dataset | 1000+ records | 1. Load list page | - Pagination works<br>- Page loads < 3s | P1 |

## 4. Compatibility Tests

Verify cross-browser and cross-device behavior.

| Case ID | Environment | Test Content | Expected Result | Priority |
|---------|-------------|--------------|-----------------|----------|
| TC-C-001 | Chrome (Latest) | Core flow | All features work | P0 |
| TC-C-002 | Firefox (Latest) | Core flow | All features work | P1 |
| TC-C-003 | Safari (Latest) | Core flow | All features work | P1 |
| TC-C-004 | Edge (Latest) | Core flow | All features work | P2 |
| TC-C-005 | iOS Safari | Core flow | All features work | P1 |
| TC-C-006 | Android Chrome | Core flow | All features work | P1 |

## 5. Security Tests

Basic security verification (not penetration testing).

| Case ID | Scenario | Steps | Expected Result | Priority |
|---------|----------|-------|-----------------|----------|
| TC-S-001 | XSS prevention | 1. Enter `<script>alert(1)</script>` in input<br>2. Submit | - Script not executed<br>- Input escaped/sanitized | P0 |
| TC-S-002 | CSRF protection | 1. Attempt cross-site request | - Request blocked<br>- CSRF token required | P0 |
| TC-S-003 | SQL injection | 1. Enter `'; DROP TABLE users;--` | - Query fails safely<br>- No data loss | P0 |

## 6. Performance Tests

Key performance metrics to verify manually.

| Metric | Target | Test Method | Priority |
|--------|--------|-------------|----------|
| Page load time | < 3s | Browser DevTools | P1 |
| API response time | < 500ms | Network tab | P1 |
| Time to interactive | < 5s | Lighthouse | P1 |
| Memory usage | No leaks | DevTools Memory | P2 |
```

## Case ID Conventions

- `TC-P-XXX`: Positive test cases
- `TC-N-XXX`: Negative test cases
- `TC-B-XXX`: Boundary test cases
- `TC-C-XXX`: Compatibility test cases
- `TC-S-XXX`: Security test cases
