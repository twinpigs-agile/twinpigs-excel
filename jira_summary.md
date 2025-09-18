Понял, давайте добавим тесты для ситуации, когда некоторые группы могут отсутствовать в словарях `estimates`, `remaining_estimates` и `postponed`, в спецификацию.

### Technical Specification for `parse_summary` and `encode_summary` Functions

#### Overview:
The `parse_summary` function parses a string according to a specified format and returns a dictionary with the results. The `encode_summary` function generates a string from the dictionary obtained from the `parse_summary` function.

### `parse_summary` Function

#### Input Data:
1. **group_names**: List of Latin letters, e.g., `['A', 'B', 'C']`.
2. **input_string**: The string to be parsed.

#### String Structure:
The string is divided into two blocks. The second block is always present, while the first block may be absent (but only entirely).

##### First Block (may be absent):
1. **prefix**: A string of 0 to 3 characters that does not contain an opening square bracket `[`. If present, it always precedes the first sub-block.
2. **First Sub-block**: Enclosed in square brackets and may contain:
   - The string `'0'` or `'?'`, indicating that all `e` values are 0 or `'?'`.
   - Several groups separated by the `+` symbol, where each group consists of a value (integer or `'?'`) and a group name (Latin letter). If a group is not mentioned, the `e` value for that group is 0.
3. **Second Sub-block** (optional): Enclosed in parentheses. The structure is identical to the first sub-block, but the values refer to `r`. If the sub-block is absent, all `r` values are equal to the corresponding `e` values. If a group is not mentioned, the `r` value for that group is 0.
4. **Third Sub-block** (optional): Enclosed in curly braces. The structure is identical to the first sub-block, but the values refer to `p`. If the sub-block is absent, all `p` values are 0. If a group is not mentioned, the `p` value for that group is 0.

##### Second Block (always present):
An arbitrary string that follows all sub-blocks. We will call it `block_2`.

#### Output Data:
The parsing results are placed in a dictionary of the form:
```python
{
    'prefix': prefix,
    'estimates': {group_names[0]: e0, group_names[1]: e1, ...},
    'remaining_estimates': {group_names[0]: r0, group_names[1]: r1, ...},
    'postponed': {group_names[0]: p0, group_names[1]: p1, ...},
    'summary': block_2
}
```

#### Examples of Strings and Expected Results:

##### Example 1: Full set of sub-blocks
**String:**
```
abc[10A+20B](30A+40B){50A+60B}Some summary text
```
**Expected Result:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 20, 'C': 0},
    'remaining_estimates': {'A': 30, 'B': 40, 'C': 0},
    'postponed': {'A': 50, 'B': 60, 'C': 0},
    'summary': 'Some summary text'
}
```

##### Example 2: Absence of the first block
**String:**
```
Some summary text
```
**Expected Result:**
```python
{
    'prefix': '',
    'estimates': {'A': '?', 'B': '?', 'C': '?'},
    'remaining_estimates': {'A': '?', 'B': '?', 'C': '?'},
    'postponed': {'A': 0, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```

##### Example 3: Absence of the second and third sub-blocks
**String:**
```
abc[10A+20B]Some summary text
```
**Expected Result:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 20, 'C': 0},
    'remaining_estimates': {'A': 10, 'B': 20, 'C': 0},
    'postponed': {'A': 0, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```

##### Example 4: Absence of the third sub-block
**String:**
```
abc[10A+20B](30A+40B)Some summary text
```
**Expected Result:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 20, 'C': 0},
    'remaining_estimates': {'A': 30, 'B': 40, 'C': 0},
    'postponed': {'A': 0, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```

##### Example 5: Absence of the second sub-block
**String:**
```
abc[10A+20B]{50A+60B}Some summary text
```
**Expected Result:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 20, 'C': 0},
    'remaining_estimates': {'A': 10, 'B': 20, 'C': 0},
    'postponed': {'A': 50, 'B': 60, 'C': 0},
    'summary': 'Some summary text'
}
```

##### Example 6: Values '0' and '?'
**String:**
```
abc[0](?){0}Some summary text
```
**Expected Result:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 0, 'B': 0, 'C': 0},
    'remaining_estimates': {'A': '?', 'B': '?', 'C': '?'},
    'postponed': {'A': 0, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```

##### Example 7: Absence of values for some groups
**String:**
```
abc[10A](30A){50A}Some summary text
```
**Expected Result:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 0, 'C': 0},
    'remaining_estimates': {'A': 30, 'B': 0, 'C': 0},
    'postponed': {'A': 50, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```

##### Example 8: Incorrect group mentions
**String:**
```
abc[10A+20M](30A+40M){50A+60M}Some summary text
```
**Expected Result:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 0, 'C': 0},
    'remaining_estimates': {'A': 30, 'B': 0, 'C': 0},
    'postponed': {'A': 50, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```

### `encode_summary` Function

#### Requirements for the `encode_summary` Function:
1. **encode_summary**: The function that takes the dictionary obtained from the `parse_summary` function and the list of groups, then generates a string.
2. If all values in a sub-block are 0, the sub-block should be represented as `0`.
3. If all values in a sub-block are `?`, the sub-block should be represented as `?`.
4. If a sub-block is absent, it is not included in the string.
5. If all values in `postponed` are 0, the sub-block `{}` is not included in the string.
6. If all values in `remaining_estimates` are equal to the corresponding values in `estimates`, the sub-block `()` is not included in the string.
7. Incorrect group mentions should be ignored.
8. Use the `get` method to access dictionary elements with default values:
   - For `prefix` and `summary`, use an empty string as the default value.
   - For `estimates`, use `?` for each group as the default value.
   - For `remaining_estimates` and `postponed`, use `0` for each group as the default value.
9. Ensure that the `encode_block` function handles cases where some groups may be missing from the dictionary.

#### Examples of Dictionaries and Expected Results:

##### Example 1: Full set of sub-blocks
**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 20, 'C': 0},
    'remaining_estimates': {'A': 30, 'B': 40, 'C': 0},
    'postponed': {'A': 50, 'B': 60, 'C': 0},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```
abc[10A+20B](30A+40B){50A+60B}Some summary text
```

##### Example 2: Absence of the first block
**Dictionary:**
```python
{
    'prefix': '',
    'estimates': {'A': '?', 'B': '?', 'C': '?'},
    'remaining_estimates': {'A': '?', 'B': '?', 'C': '?'},
    'postponed': {'A': 0, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```
[?]Some summary text
```

##### Example 3: Absence of the second and third sub-blocks
**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 20, 'C': 0},
    'remaining_estimates': {'A': 10, 'B': 20, 'C': 0},
    'postponed': {'A': 0, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```
abc[10A+20B]Some summary text
```

##### Example 4: Absence of the third sub-block
**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 20, 'C': 0},
    'remaining_estimates': {'A': 30, 'B': 40, 'C': 0},
    'postponed': {'A': 0, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```
abc[10A+20B](30A+40B)Some summary text
```

##### Example 5: Absence of the second sub-block
**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 20, 'C': 0},
    'remaining_estimates': {'A': 10, 'B': 20, 'C': 0},
    'postponed': {'A': 50, 'B': 60, 'C': 0},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```
abc[10A+20B]{50A+60B}Some summary text
```

##### Example 6: Values '0' and '?'
**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 0, 'B': 0, 'C': 0},
    'remaining_estimates': {'A': '?', 'B': '?', 'C': '?'},
    'postponed': {'A': 0, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```
abc[0](?)Some summary text
```

##### Example 7: Absence of values for some groups
**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 0, 'C': 0},
    'remaining_estimates': {'A': 30, 'B': 0, 'C': 0},
    'postponed': {'A': 50, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```
abc[10A](30A){50A}Some summary text
```

##### Example 8: Incorrect group mentions
**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 0, 'C': 0, 'M': 20},
    'remaining_estimates': {'A': 30, 'B': 0, 'C': 0, 'M': 40},
    'postponed': {'A': 50, 'B': 0, 'C': 0, 'M': 60},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```
abc[10A](30A){50A}Some summary text
```

##### Example 9: Missing groups in dictionaries
**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 20},
    'remaining_estimates': {'A': 30, 'B': 40},
    'postponed': {'A': 50, 'B': 60},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```
abc[10A+20B](30A+40B){50A+60B}Some summary text
```

**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10},
    'remaining_estimates': {'A': 30},
    'postponed': {'A': 50},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```
abc[10A](30A){50A}Some summary text
```

#### Round-trip Test:
The following test ensures that the original dictionary, when encoded and then parsed, will be equal to the result.

##### Example 10: Round-trip test
**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 20, 'C': 0},
    'remaining_estimates': {'A': 30, 'B': 40, 'C': 0},
    'postponed': {'A': 50, 'B': 60, 'C': 0},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```python
parse_summary(['A', 'B', 'C'], encode_summary(['A', 'B', 'C'], summary_dict)) == summary_dict
```

**Dictionary:**
```python
{
    'prefix': '',
    'estimates': {'A': '?', 'B': '?', 'C': '?'},
    'remaining_estimates': {'A': '?', 'B': '?', 'C': '?'},
    'postponed': {'A': 0, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```python
parse_summary(['A', 'B', 'C'], encode_summary(['A', 'B', 'C'], summary_dict)) == summary_dict
```

**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 20, 'C': 0},
    'remaining_estimates': {'A': 10, 'B': 20, 'C': 0},
    'postponed': {'A': 0, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```python
parse_summary(['A', 'B', 'C'], encode_summary(['A', 'B', 'C'], summary_dict)) == summary_dict
```

**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 20, 'C': 0},
    'remaining_estimates': {'A': 30, 'B': 40, 'C': 0},
    'postponed': {'A': 0, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```python
parse_summary(['A', 'B', 'C'], encode_summary(['A', 'B', 'C'], summary_dict)) == summary_dict
```

**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 10, 'B': 20, 'C': 0},
    'remaining_estimates': {'A': 10, 'B': 20, 'C': 0},
    'postponed': {'A': 50, 'B': 60, 'C': 0},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```python
parse_summary(['A', 'B', 'C'], encode_summary(['A', 'B', 'C'], summary_dict)) == summary_dict
```

**Dictionary:**
```python
{
    'prefix': 'abc',
    'estimates': {'A': 0, 'B': 0, 'C': 0},
    'remaining_estimates': {'A': '?', 'B': '?', 'C': '?'},
    'postponed': {'A': 0, 'B': 0, 'C': 0},
    'summary': 'Some summary text'
}
```
**Expected Result:**
```python
parse_summary(['A', 'B', 'C'], encode_summary
