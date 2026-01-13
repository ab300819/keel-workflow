# UI Automation Test Template

Use this template to generate `docs/prd/03-test-e2e.md`.

```markdown
# UI Automation Test Plan: <Feature Name>

## Test Framework

- **Framework**: <Playwright / Cypress / Selenium / Appium>
- **Language**: <TypeScript / JavaScript / Python>
- **Environment**: <Browser versions / Devices>

## Browser/Device Matrix

| Browser/Device | Version | Priority |
|----------------|---------|----------|
| Chrome | Latest | P0 |
| Firefox | Latest | P1 |
| Safari | Latest | P1 |
| Mobile Chrome | Android 10+ | P1 |
| Mobile Safari | iOS 14+ | P1 |

## Core Scenario Coverage

All P0 scenarios must be covered by automation.

### <User Flow Name>

| Case ID | Scenario | Steps | Assertions | Priority |
|---------|----------|-------|------------|----------|
| E2E-001 | <scenario name> | 1. Navigate to /path<br>2. Click button<br>3. Fill form | - Page title is "X"<br>- Success message shown | P0 |
| E2E-002 | <scenario name> | 1. ...<br>2. ... | - ... | P0 |

**Test Code Example**:
```typescript
test('should complete user registration', async ({ page }) => {
  // Arrange
  await page.goto('/register');

  // Act
  await page.fill('[data-testid="email"]', 'test@example.com');
  await page.fill('[data-testid="password"]', 'SecurePass123!');
  await page.click('[data-testid="submit"]');

  // Assert
  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('[data-testid="welcome"]')).toBeVisible();
});
```

## Test Data Management

### Data Preparation

| Scenario | Required Data | Preparation Method | Cleanup |
|----------|---------------|-------------------|---------|
| Login | Test user account | API seeding before test | Delete after suite |
| Checkout | Product, cart items | Database fixtures | Transaction rollback |

### Data Isolation

```typescript
test.beforeEach(async ({ request }) => {
  // Create isolated test data
  const user = await request.post('/api/test/users', {
    data: { email: `test-${Date.now()}@example.com` }
  });
  testUserId = user.id;
});

test.afterEach(async ({ request }) => {
  // Cleanup test data
  await request.delete(`/api/test/users/${testUserId}`);
});
```

## Page Object Model

### Page Objects Structure

```
tests/
├── e2e/
│   ├── pages/
│   │   ├── LoginPage.ts
│   │   ├── DashboardPage.ts
│   │   └── CheckoutPage.ts
│   ├── fixtures/
│   │   └── test-data.ts
│   └── specs/
│       ├── auth.spec.ts
│       └── checkout.spec.ts
```

### Page Object Example

```typescript
// pages/LoginPage.ts
export class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.page.fill('[data-testid="email"]', email);
    await this.page.fill('[data-testid="password"]', password);
    await this.page.click('[data-testid="submit"]');
  }

  async expectError(message: string) {
    await expect(this.page.locator('.error')).toHaveText(message);
  }
}
```

## Execution

### Run Commands

```bash
# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test tests/e2e/auth.spec.ts

# Run with UI mode
npx playwright test --ui

# Run in specific browser
npx playwright test --project=chromium

# Generate report
npx playwright show-report
```

### CI Configuration

```yaml
# GitHub Actions example
e2e-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Install dependencies
      run: npm ci
    - name: Install Playwright
      run: npx playwright install --with-deps
    - name: Run E2E tests
      run: npx playwright test
    - name: Upload report
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: playwright-report
        path: playwright-report/
```

## Retry and Stability

```typescript
// playwright.config.ts
export default defineConfig({
  retries: process.env.CI ? 2 : 0,
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
});
```
```

## Case ID Conventions

- `E2E-XXX`: End-to-end test cases
- Format: `E2E-{flow}-{number}`
- Example: `E2E-AUTH-001`, `E2E-CHECKOUT-002`
