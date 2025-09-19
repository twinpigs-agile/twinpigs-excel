# Twin Pigs Jira Driver Release Notes

## Version: 5.1

### Changes:
1. **Compatibility check for Jira Driver and Calculator versions**:
   - Since now, incompatible versions do not work together, TO JIRA/FROM JIRA gives an error. No data corruption happens in that case.

2. **Errors processing**:
   - Now exception strings are returned with code 200, not 400. That allows the Excel script to process results and show correct status.


## Version: 5.0

### Changes:
1. **Support for Saving Data in Summary Field from Postponed Column**:
   - The application now supports saving data from the "Postponed" column into the "Summary" field.

2. **Support for Using Question Mark as an Estimate**:
   - When importing issues from Jira that have not been previously estimated, all estimates will be assigned a value of "?". These values do not affect calculations (equivalent to a value of 0) but mark tasks that have not been estimated.

### Warning:
- **Mandatory Script Update**:
  - This version requires the script (triggered by the RUN button) to be updated to version 5. Using the old script version may result in data corruption. The author can update the script in your worksheets upon request.
