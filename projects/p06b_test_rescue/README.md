# Project 6b: Test Rescue

Part 6 · Professional Python. The full brief, hints, and rubric are on the course site at
`docs/projects/p06b-test-rescue.html` (`pixi run serve`).

## Scenario

You have inherited `invoicer`, a small invoicing tool with no tests. It reads environment variables and the clock, picks
random numbers, calls a remote service with retries, writes files, and keeps global state. Your job is to write the test
suite. You do not change the package.

## How grading works

```sh
pixi run start p06b     # copies the code to work/p06b_test_rescue/
# write tests in work/p06b_test_rescue/tests/
pixi run grade p06b
```

The grader copies a pristine `invoicer` and your `tests/` directory into a sandbox and checks that your suite:

- passes on the original code, blocks no real behavior, and opens no network connections
- finishes in under 20 seconds, so `time.sleep` must be patched
- reaches at least 90% coverage of the package
- still passes with `INVOICER_*` variables already set, with a different real date, and in reverse order
- leaves no files behind
- fails on each of 28 versions of the package that contain a planted bug

Edits you make to `invoicer` are ignored, because the grader always tests the original.
