import re

def parse_summary(group_names, input_string):
    """
    Parses a string according to the specified format and returns a dictionary with the results.

    Args:
        group_names (list): List of Latin letters, e.g., ['A', 'B', 'C'].
        input_string (str): The string to be parsed.

    Returns:
        dict: Dictionary with the parsing results.

    Examples:
        >>> parse_summary(['A', 'B', 'C'], 'abc[10A+20B](30A+40B){50A+60B}Some summary text')
        {'prefix': 'abc', 'estimates': {'A': 10, 'B': 20, 'C': 0}, 'remaining_estimates': {'A': 30, 'B': 40, 'C': 0}, 'postponed': {'A': 50, 'B': 60, 'C': 0}, 'summary': 'Some summary text'}

        >>> parse_summary(['A', 'B', 'C'], 'Some summary text')
        {'prefix': '', 'estimates': {'A': '?', 'B': '?', 'C': '?'}, 'remaining_estimates': {'A': '?', 'B': '?', 'C': '?'}, 'postponed': {'A': 0, 'B': 0, 'C': 0}, 'summary': 'Some summary text'}

        >>> parse_summary(['A', 'B', 'C'], 'abc[10A+20B]Some summary text')
        {'prefix': 'abc', 'estimates': {'A': 10, 'B': 20, 'C': 0}, 'remaining_estimates': {'A': 10, 'B': 20, 'C': 0}, 'postponed': {'A': 0, 'B': 0, 'C': 0}, 'summary': 'Some summary text'}

        >>> parse_summary(['A', 'B', 'C'], 'abc[10A+20B](30A+40B)Some summary text')
        {'prefix': 'abc', 'estimates': {'A': 10, 'B': 20, 'C': 0}, 'remaining_estimates': {'A': 30, 'B': 40, 'C': 0}, 'postponed': {'A': 0, 'B': 0, 'C': 0}, 'summary': 'Some summary text'}

        >>> parse_summary(['A', 'B', 'C'], 'abc[10A+20B]{50A+60B}Some summary text')
        {'prefix': 'abc', 'estimates': {'A': 10, 'B': 20, 'C': 0}, 'remaining_estimates': {'A': 10, 'B': 20, 'C': 0}, 'postponed': {'A': 50, 'B': 60, 'C': 0}, 'summary': 'Some summary text'}

        >>> parse_summary(['A', 'B', 'C'], 'abc[0](?){0}Some summary text')
        {'prefix': 'abc', 'estimates': {'A': 0, 'B': 0, 'C': 0}, 'remaining_estimates': {'A': '?', 'B': '?', 'C': '?'}, 'postponed': {'A': 0, 'B': 0, 'C': 0}, 'summary': 'Some summary text'}

        >>> parse_summary(['A', 'B', 'C'], 'abc[10A](30A){50A}Some summary text')
        {'prefix': 'abc', 'estimates': {'A': 10, 'B': 0, 'C': 0}, 'remaining_estimates': {'A': 30, 'B': 0, 'C': 0}, 'postponed': {'A': 50, 'B': 0, 'C': 0}, 'summary': 'Some summary text'}

        >>> parse_summary(['A', 'B', 'C'], 'abc[10A+20M](30A+40M){50A+60M}Some summary text')
        {'prefix': 'abc', 'estimates': {'A': 10, 'B': 0, 'C': 0}, 'remaining_estimates': {'A': 30, 'B': 0, 'C': 0}, 'postponed': {'A': 50, 'B': 0, 'C': 0}, 'summary': 'Some summary text'}
    """
    # Regular expression for parsing the string
    pattern = re.compile(r'^(?P<prefix>[^\[]{0,3})?\[(?P<estimate>[^\]]+)\](\((?P<remaining_estimate>[^\)]+)\))?(\{(?P<postponed>[^\}]+)\})?(?P<summary>.*)$')

    # Parse the string
    match = pattern.match(input_string)
    if match:
        prefix = match.group('prefix') or ''
        estimate_str = match.group('estimate')
        remaining_estimate_str = match.group('remaining_estimate')
        postponed_str = match.group('postponed')
        summary = match.group('summary').strip()

        def parse_block(block_str, default_value):
            if block_str == '0':
                return {name: 0 for name in group_names}
            elif block_str == '?':
                return {name: '?' for name in group_names}
            else:
                values = {name: default_value for name in group_names}
                if block_str:
                    for part in block_str.split('+'):
                        value, name = re.match(r'(\d+|\?)([A-Z])', part).groups()
                        if name in group_names:
                            values[name] = int(value) if value.isdigit() else value
                return values

        estimates = parse_block(estimate_str, 0)
        remaining_estimates = parse_block(remaining_estimate_str, 0)

        # If the second sub-block is missing, all remaining_estimates values are equal to the corresponding estimates values
        if remaining_estimate_str is None:
            remaining_estimates = estimates.copy()

        postponed = parse_block(postponed_str, 0)

        return {
            'prefix': prefix,
            'estimates': estimates,
            'remaining_estimates': remaining_estimates,
            'postponed': postponed,
            'summary': summary
        }
    else:
        return {
            'prefix': '',
            'estimates': {name: '?' for name in group_names},
            'remaining_estimates': {name: '?' for name in group_names},
            'postponed': {name: 0 for name in group_names},
            'summary': input_string.strip()
        }

def encode_summary(group_names, summary_dict):
    """
    Generates a string from the dictionary obtained from the parse_summary function.

    Args:
        group_names (list): List of Latin letters, e.g., ['A', 'B', 'C'].
        summary_dict (dict): Dictionary with the parsing results.

    Returns:
        str: Generated string.

    Examples:
        >>> encode_summary(['A', 'B', 'C'], {'prefix': 'abc', 'estimates': {'A': 10, 'B': 20, 'C': 0}, 'remaining_estimates': {'A': 30, 'B': 40, 'C': 0}, 'postponed': {'A': 50, 'B': 60, 'C': 0}, 'summary': 'Some summary text'})
        'abc[10A+20B](30A+40B){50A+60B}Some summary text'

        >>> encode_summary(['A', 'B', 'C'], {'prefix': '', 'estimates': {'A': '?', 'B': '?', 'C': '?'}, 'remaining_estimates': {'A': '?', 'B': '?', 'C': '?'}, 'postponed': {'A': 0, 'B': 0, 'C': 0}, 'summary': 'Some summary text'})
        '[?]Some summary text'

        >>> encode_summary(['A', 'B', 'C'], {'prefix': 'abc', 'estimates': {'A': 10, 'B': 20, 'C': 0}, 'remaining_estimates': {'A': 10, 'B': 20, 'C': 0}, 'postponed': {'A': 0, 'B': 0, 'C': 0}, 'summary': 'Some summary text'})
        'abc[10A+20B]Some summary text'

        >>> encode_summary(['A', 'B', 'C'], {'prefix': 'abc', 'estimates': {'A': 10, 'B': 20, 'C': 0}, 'remaining_estimates': {'A': 30, 'B': 40, 'C': 0}, 'postponed': {'A': 0, 'B': 0, 'C': 0}, 'summary': 'Some summary text'})
        'abc[10A+20B](30A+40B)Some summary text'

        >>> encode_summary(['A', 'B', 'C'], {'prefix': 'abc', 'estimates': {'A': 10, 'B': 20, 'C': 0}, 'remaining_estimates': {'A': 10, 'B': 20, 'C': 0}, 'postponed': {'A': 50, 'B': 60, 'C': 0}, 'summary': 'Some summary text'})
        'abc[10A+20B]{50A+60B}Some summary text'

        >>> encode_summary(['A', 'B', 'C'], {'prefix': 'abc', 'estimates': {'A': 0, 'B': 0, 'C': 0}, 'remaining_estimates': {'A': '?', 'B': '?', 'C': '?'}, 'postponed': {'A': 0, 'B': 0, 'C': 0}, 'summary': 'Some summary text'})
        'abc[0](?)Some summary text'

        >>> encode_summary(['A', 'B', 'C'], {'prefix': 'abc', 'estimates': {'A': 10, 'B': 0, 'C': 0}, 'remaining_estimates': {'A': 30, 'B': 0, 'C': 0}, 'postponed': {'A': 50, 'B': 0, 'C': 0}, 'summary': 'Some summary text'})
        'abc[10A](30A){50A}Some summary text'

        >>> encode_summary(['A', 'B', 'C'], {'prefix': 'abc', 'estimates': {'A': 10, 'B': 0, 'C': 0}, 'remaining_estimates': {'A': 30, 'B': 0, 'C': 0}, 'postponed': {'A': 50, 'B': 0, 'C': 0}, 'summary': 'Some summary text'})
        'abc[10A](30A){50A}Some summary text'

        >>> encode_summary(['A', 'B', 'C'], {'prefix': 'abc', 'estimates': {'A': 10, 'B': 0, 'C': 0, 'M': 20}, 'remaining_estimates': {'A': 30, 'B': 0, 'C': 0, 'M': 40}, 'postponed': {'A': 50, 'B': 0, 'C': 0, 'M': 60}, 'summary': 'Some summary text'})
        'abc[10A](30A){50A}Some summary text'

        >>> encode_summary(['A', 'B', 'C'], {'prefix': 'abc', 'estimates': {'A': 10, 'B': 20}, 'remaining_estimates': {'A': 30, 'B': 40}, 'postponed': {'A': 50, 'B': 60}, 'summary': 'Some summary text'})
        'abc[10A+20B](30A+40B){50A+60B}Some summary text'

        >>> encode_summary(['A', 'B', 'C'], {'prefix': 'abc', 'estimates': {'A': 10}, 'remaining_estimates': {'A': 30}, 'postponed': {'A': 50}, 'summary': 'Some summary text'})
        'abc[10A](30A){50A}Some summary text'

        >>> summary_dict = {'prefix': 'abc', 'estimates': {'A': 10, 'B': 20, 'C': 0}, 'remaining_estimates': {'A': 30, 'B': 40, 'C': 0}, 'postponed': {'A': 50, 'B': 60, 'C': 0}, 'summary': 'Some summary text'}
        >>> parse_summary(['A', 'B', 'C'], encode_summary(['A', 'B', 'C'], summary_dict)) == summary_dict
        True

        >>> summary_dict = {'prefix': '', 'estimates': {'A': '?', 'B': '?', 'C': '?'}, 'remaining_estimates': {'A': '?', 'B': '?', 'C': '?'}, 'postponed': {'A': 0, 'B': 0, 'C': 0}, 'summary': 'Some summary text'}
        >>> parse_summary(['A', 'B', 'C'], encode_summary(['A', 'B', 'C'], summary_dict)) == summary_dict
        True

        >>> summary_dict = {'prefix': 'abc', 'estimates': {'A': 10, 'B': 20, 'C': 0}, 'remaining_estimates': {'A': 10, 'B': 20, 'C': 0}, 'postponed': {'A': 0, 'B': 0, 'C': 0}, 'summary': 'Some summary text'}
        >>> parse_summary(['A', 'B', 'C'], encode_summary(['A', 'B', 'C'], summary_dict)) == summary_dict
        True

        >>> summary_dict = {'prefix': 'abc', 'estimates': {'A': 10, 'B': 20, 'C': 0}, 'remaining_estimates': {'A': 30, 'B': 40, 'C': 0}, 'postponed': {'A': 0, 'B': 0, 'C': 0}, 'summary': 'Some summary text'}
        >>> parse_summary(['A', 'B', 'C'], encode_summary(['A', 'B', 'C'], summary_dict)) == summary_dict
        True

        >>> summary_dict = {'prefix': 'abc', 'estimates': {'A': 10, 'B': 20, 'C': 0}, 'remaining_estimates': {'A': 10, 'B': 20, 'C': 0}, 'postponed': {'A': 50, 'B': 60, 'C': 0}, 'summary': 'Some summary text'}
        >>> parse_summary(['A', 'B', 'C'], encode_summary(['A', 'B', 'C'], summary_dict)) == summary_dict
        True

        >>> summary_dict = {'prefix': 'abc', 'estimates': {'A': 0, 'B': 0, 'C': 0}, 'remaining_estimates': {'A': '?', 'B': '?', 'C': '?'}, 'postponed': {'A': 0, 'B': 0, 'C': 0}, 'summary': 'Some summary text'}
        >>> parse_summary(['A', 'B', 'C'], encode_summary(['A', 'B', 'C'], summary_dict)) == summary_dict
        True

        >>> summary_dict = {'prefix': 'abc', 'estimates': {'A': 10, 'B': 0, 'C': 0}, 'remaining_estimates': {'A': 30, 'B': 0, 'C': 0}, 'postponed': {'A': 50, 'B': 0, 'C': 0}, 'summary': 'Some summary text'}
        >>> parse_summary(['A', 'B', 'C'], encode_summary(['A', 'B', 'C'], summary_dict)) == summary_dict
        True

        >>> summary_dict = {'prefix': 'abc', 'estimates': {'A': 10, 'B': 0, 'C': 0}, 'remaining_estimates': {'A': 30, 'B': 0, 'C': 0}, 'postponed': {'A': 50, 'B': 0, 'C': 0}, 'summary': 'Some summary text'}
        >>> parse_summary(['A', 'B', 'C'], encode_summary(['A', 'B', 'C'], summary_dict)) == summary_dict
        True
    """
    def encode_block(block_dict):
        values = [block_dict.get(name, 0) for name in group_names]
        if all(v == 0 for v in values):
            return '0'
        elif all(v == '?' for v in values):
            return '?'
        else:
            return '+'.join(f'{block_dict.get(name, 0)}{name}' for name in group_names if block_dict.get(name, 0) != 0)

    prefix = summary_dict.get('prefix', '')
    estimates = summary_dict.get('estimates', {name: '?' for name in group_names})
    remaining_estimates = summary_dict.get('remaining_estimates', {name: 0 for name in group_names})
    postponed = summary_dict.get('postponed', {name: 0 for name in group_names})
    summary = summary_dict.get('summary', '')

    result = f'{prefix}[{encode_block(estimates)}]'
    if remaining_estimates != estimates:
        result += f'({encode_block(remaining_estimates)})'
    postponed_block = encode_block(postponed)
    if postponed_block != '0':
        result += f'{{{postponed_block}}}'
    result += summary

    return result

if __name__ == "__main__":
    import doctest
    doctest.testmod()
