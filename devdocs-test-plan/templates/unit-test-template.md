# Unit Test Template

Use this template to generate `docs/prd/03-test-unit.md`.

```markdown
# Unit Test Plan: <Feature Name>

## Coverage Requirements

- **Line Coverage**: >= 80%
- **Branch Coverage**: >= 80%

## Test Scope

| Module/File | Core Functions | Test Focus |
|-------------|----------------|------------|
| `src/services/xxx.ts` | `functionName()` | <focus description> |
| `src/utils/xxx.ts` | `helperFn()` | <focus description> |

## Test Cases

### <Module Name>

#### <Function Name>

| Case ID | Scenario | Input | Expected Output | Priority |
|---------|----------|-------|-----------------|----------|
| UT-001 | Normal case | `{ valid: true }` | `{ success: true }` | P0 |
| UT-002 | Boundary case | `{ value: 0 }` | `{ result: 0 }` | P1 |
| UT-003 | Error case | `null` | `throws InvalidInputError` | P0 |
| UT-004 | Edge case | `{ value: MAX_INT }` | `{ overflow: true }` | P1 |

**Test Code Example**:
```typescript
describe('functionName', () => {
  it('should return success for valid input', () => {
    const result = functionName({ valid: true });
    expect(result).toEqual({ success: true });
  });

  it('should throw error for null input', () => {
    expect(() => functionName(null)).toThrow(InvalidInputError);
  });
});
```

## Mock Strategy

| Dependency | Mock Type | Description |
|------------|-----------|-------------|
| Database | Mock | Use in-memory mock |
| External API | Stub | Return predefined responses |
| Logger | Spy | Verify log calls |
| Time | Mock | Use fake timers |

### Mock Examples

**Database Mock**:
```typescript
const mockDb = {
  query: jest.fn().mockResolvedValue([{ id: 1 }]),
  insert: jest.fn().mockResolvedValue({ insertId: 1 }),
};
```

**External API Stub**:
```typescript
jest.mock('./externalApi', () => ({
  fetchData: jest.fn().mockResolvedValue({ data: 'mocked' }),
}));
```

## Test Data

### Fixtures

| Fixture Name | Description | Location |
|--------------|-------------|----------|
| validUser | Standard user object | `__fixtures__/user.ts` |
| invalidInput | Various invalid inputs | `__fixtures__/invalid.ts` |

### Factory Functions

```typescript
// Create test user with overrides
const createTestUser = (overrides = {}) => ({
  id: 'test-id',
  name: 'Test User',
  email: 'test@example.com',
  ...overrides,
});
```

## Execution

### Run Commands

```bash
# Run all unit tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific file
npm test -- src/services/xxx.test.ts

# Watch mode
npm test -- --watch
```

### CI Integration

```yaml
# Example GitHub Actions
- name: Run Unit Tests
  run: npm test -- --coverage --ci

- name: Check Coverage
  run: |
    COVERAGE=$(npm test -- --coverage --json | jq '.total.lines.pct')
    if [ "$COVERAGE" -lt 80 ]; then exit 1; fi
```
```

## Case ID Conventions

- `UT-XXX`: Unit test cases
- Format: `UT-{module}-{number}`
- Example: `UT-AUTH-001`, `UT-USER-002`
