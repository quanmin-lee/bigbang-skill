# End-to-End Verification Results

## Test 1: Amount column summary

**Command:** `python -m excel_summary.cli --input sample.xlsx --column amount --output actual_output.csv`

**Output:**
```
stat,value
sum,1400.0
mean,175.0
max,300.0
min,0.0
unique_count,8
```

**Expected:** sum=100+200+150+300+250+180+220+0=1400, mean=1400/8=175, max=300, min=0, unique=8
**Result:** PASS

## Test 2: Score column (with None values)

**Command:** `python -m excel_summary.cli --input sample.xlsx --column score --output score_output.csv`

**Output:**
```
stat,value
sum,754.0
mean,83.77777777777777
max,95.0
min,60.0
unique_count,9
```

**Expected:** sum=85+92+78+95+88+91+76+89+60=754, mean=754/9=83.78, max=95, min=60, unique=9
**Result:** PASS

## Test 3: Non-existent file

**Command:** `python -m excel_summary.cli --input nonexistent.xlsx --column amount`

**Output:** `Error: File not found: nonexistent.xlsx` (exit code 1)
**Result:** PASS

## Test 4: Non-existent column

**Command:** `python -m excel_summary.cli --input sample.xlsx --column nonexistent`

**Output:** `Error: Column 'nonexistent' not found in the worksheet` (exit code 1)
**Result:** PASS

## Test 5: Missing required arguments

**Command:** `python -m excel_summary.cli`

**Output:** argparse usage message displayed (exit code 2)
**Result:** PASS

## Test Suite

```
python -m pytest tests/ -v  →  15 passed in 0.23s
```

## Final Verdict

All 5 end-to-end tests pass. Full test suite: 15/15 passing. All edge cases (empty column, non-numeric data, missing file, missing arguments) are handled gracefully.

**Status: SUCCESS**
