# Eval report: Categorization text run

- **eval**: `IT Ticket Categorization` (`eval_52b2099ada1c4f6b92fbdc52`)
- **run**: `evalrun_e86fcd354c004583aca7fb93`
- **status**: `completed`
- **model**: `ticket-stub-v1`
- **pass rate**: **100%** (6/6; failed=0, errored=0)

## Per-criteria results

| Criteria | Passed | Failed |
|----------|--------|--------|
| `Match output to human label-3a7f4d5653d1` | 6 | 0 |
| `Output is a valid category-ab7724f348dd` | 6 | 0 |

## Samples

### #1 — PASS

- item: `{'ticket_text': "My monitor won't turn on!", 'correct_label': 'Hardware'}`
- output: `Hardware`
- grader `Match output to human label`: passed=True score=1.00 — eq: 'Hardware' vs 'Hardware'
- grader `Output is a valid category`: passed=True score=1.00 — 'Hardware' in ('Hardware', 'Software', 'Other')

### #2 — PASS

- item: `{'ticket_text': "I'm in vim and I can't quit!", 'correct_label': 'Software'}`
- output: `Software`
- grader `Match output to human label`: passed=True score=1.00 — eq: 'Software' vs 'Software'
- grader `Output is a valid category`: passed=True score=1.00 — 'Software' in ('Hardware', 'Software', 'Other')

### #3 — PASS

- item: `{'ticket_text': 'Best restaurants in Cleveland?', 'correct_label': 'Other'}`
- output: `Other`
- grader `Match output to human label`: passed=True score=1.00 — eq: 'Other' vs 'Other'
- grader `Output is a valid category`: passed=True score=1.00 — 'Other' in ('Hardware', 'Software', 'Other')

### #4 — PASS

- item: `{'ticket_text': 'Laptop battery swells and keyboard stops working', 'correct_label': 'Hardware'}`
- output: `Hardware`
- grader `Match output to human label`: passed=True score=1.00 — eq: 'Hardware' vs 'Hardware'
- grader `Output is a valid category`: passed=True score=1.00 — 'Hardware' in ('Hardware', 'Software', 'Other')

### #5 — PASS

- item: `{'ticket_text': 'Excel crashes when I open the budget spreadsheet', 'correct_label': 'Software'}`
- output: `Software`
- grader `Match output to human label`: passed=True score=1.00 — eq: 'Software' vs 'Software'
- grader `Output is a valid category`: passed=True score=1.00 — 'Software' in ('Hardware', 'Software', 'Other')

### #6 — PASS

- item: `{'ticket_text': 'Where should we go for team lunch?', 'correct_label': 'Other'}`
- output: `Other`
- grader `Match output to human label`: passed=True score=1.00 — eq: 'Other' vs 'Other'
- grader `Output is a valid category`: passed=True score=1.00 — 'Other' in ('Hardware', 'Software', 'Other')

## Usage

```json
[{'model_name': 'ticket-stub-v1', 'invocation_count': 6, 'prompt_tokens': 224, 'completion_tokens': 6, 'total_tokens': 230, 'cached_tokens': 0}]
```

## Research notes

- Treat this report as a **signal**, not a certificate of safety.
- Calibrate automated graders against human labels before scaling.
- Grow the dataset with production edge cases (logs → eval items).
