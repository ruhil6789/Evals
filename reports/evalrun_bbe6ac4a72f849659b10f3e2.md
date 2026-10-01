# Eval report: weak-stub

- **eval**: `IT Ticket Categorization` (`eval_52b2099ada1c4f6b92fbdc52`)
- **run**: `evalrun_bbe6ac4a72f849659b10f3e2`
- **status**: `completed`
- **model**: `ticket-stub-always-other`
- **pass rate**: **33%** (2/6; failed=4, errored=0)

## Per-criteria results

| Criteria | Passed | Failed |
|----------|--------|--------|
| `Match output to human label-3a7f4d5653d1` | 2 | 4 |
| `Output is a valid category-ab7724f348dd` | 6 | 0 |

## Samples

### #1 — FAIL

- item: `{'ticket_text': "My monitor won't turn on!", 'correct_label': 'Hardware'}`
- output: `Other`
- grader `Match output to human label`: passed=False score=0.00 — eq: 'Other' vs 'Hardware'
- grader `Output is a valid category`: passed=True score=1.00 — 'Other' in ('Hardware', 'Software', 'Other')

### #2 — FAIL

- item: `{'ticket_text': "I'm in vim and I can't quit!", 'correct_label': 'Software'}`
- output: `Other`
- grader `Match output to human label`: passed=False score=0.00 — eq: 'Other' vs 'Software'
- grader `Output is a valid category`: passed=True score=1.00 — 'Other' in ('Hardware', 'Software', 'Other')

### #3 — PASS

- item: `{'ticket_text': 'Best restaurants in Cleveland?', 'correct_label': 'Other'}`
- output: `Other`
- grader `Match output to human label`: passed=True score=1.00 — eq: 'Other' vs 'Other'
- grader `Output is a valid category`: passed=True score=1.00 — 'Other' in ('Hardware', 'Software', 'Other')

### #4 — FAIL

- item: `{'ticket_text': 'Laptop battery swells and keyboard stops working', 'correct_label': 'Hardware'}`
- output: `Other`
- grader `Match output to human label`: passed=False score=0.00 — eq: 'Other' vs 'Hardware'
- grader `Output is a valid category`: passed=True score=1.00 — 'Other' in ('Hardware', 'Software', 'Other')

### #5 — FAIL

- item: `{'ticket_text': 'Excel crashes when I open the budget spreadsheet', 'correct_label': 'Software'}`
- output: `Other`
- grader `Match output to human label`: passed=False score=0.00 — eq: 'Other' vs 'Software'
- grader `Output is a valid category`: passed=True score=1.00 — 'Other' in ('Hardware', 'Software', 'Other')

### #6 — PASS

- item: `{'ticket_text': 'Where should we go for team lunch?', 'correct_label': 'Other'}`
- output: `Other`
- grader `Match output to human label`: passed=True score=1.00 — eq: 'Other' vs 'Other'
- grader `Output is a valid category`: passed=True score=1.00 — 'Other' in ('Hardware', 'Software', 'Other')

## Usage

```json
[{'model_name': 'ticket-stub-always-other', 'invocation_count': 6, 'prompt_tokens': 224, 'completion_tokens': 6, 'total_tokens': 230, 'cached_tokens': 0}]
```

## Research notes

- Treat this report as a **signal**, not a certificate of safety.
- Calibrate automated graders against human labels before scaling.
- Grow the dataset with production edge cases (logs → eval items).
