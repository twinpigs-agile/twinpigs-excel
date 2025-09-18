import asyncio
import json
import argparse
import sys
import re
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode
import aiohttp
from base64 import b64encode

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')





################################# THE PARSER/ENCODER GENERATED BLOCK #################################
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

################################# THE END OF THE GENERATED BLOCK #################################




class RequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        parsed_path = urlparse(self.path)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        logging.info(f"Received POST request on {parsed_path.path} with data: {data}")

        if parsed_path.path == '/query_issues':
            asyncio.run(self.handle_query_issues(data))
        elif parsed_path.path == '/update_issues':
            asyncio.run(self.handle_update_issues(data))
        else:
            self.send_response(404)
            self.end_headers()

    async def handle_query_issues(self, data):
        jql = data.get('jql', '')
        resource_groups = data.get('resource_groups', [])
        if not jql:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing jql parameter'}).encode('utf-8'))
            return

        query_params = urlencode({'jql': jql, 'maxResults': 1000})
        jira_url = f'{self.server.jira_server}/rest/api/2/search?{query_params}'
        response = await self.call_external_api(jira_url)

        # Parsing the Jira request results
        processed_response = self.process_jira_response(response, resource_groups)

        logging.info(f"Processed response for query_issues: {processed_response}")

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(processed_response).encode('utf-8'))

    async def handle_update_issues(self, data):
        issues = data.get('issues', [])
        jql = data.get('jql', '')
        resource_groups = data.get('resource_groups', [])

        if not issues or not jql:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing issues or jql parameter'}).encode('utf-8'))
            return

        input_summaries = {issue['key']: encode_summary(resource_groups, issue)for issue in issues}

        query_params = urlencode({'jql': jql, 'maxResults': 1000})
        jira_url = f'{self.server.jira_server}/rest/api/2/search?{query_params}'
        response = await self.call_external_api(jira_url)
        jira_summaries = {issue['key']: issue['fields']['summary'] for issue in response.get('issues', [])}

        keys_to_update = [key for key, summary in input_summaries.items() if
                          key not in jira_summaries or jira_summaries[key] != summary]

        for key in keys_to_update:
            await self.update_jira_summary(key, input_summaries[key])

        logging.info(f"Updated keys: {keys_to_update}")

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'updated_keys': keys_to_update}).encode('utf-8'))

    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.server.token}' if self.server.token else ('Basic ' + b64encode(f"{self.server.user}:{self.server.password}".encode()).decode()),
            'Content-Type': 'application/json'
        }

    async def update_jira_summary(self, key, summary):
        jira_url = f'{self.server.jira_server}/rest/api/2/issue/{key}'
        data = {
            'fields': {
                'summary': summary
            }
        }
        headers = self.get_headers()
        async with aiohttp.ClientSession() as session:
            async with session.put(jira_url, json=data, headers=headers) as resp:
                if resp.status != 204:
                    logging.error(f"Failed to update summary for {key}: {resp.status}")

    async def call_external_api(self, url, data=None):
        headers = self.get_headers()
        async with aiohttp.ClientSession() as session:
            if data:
                async with session.post(url, json=data, headers=headers) as resp:
                    if resp.status != 200:
                        raise Exception("Jira POST failed")
                    response = await resp.json()
                    logging.info(
                        f"Called external API with POST to {url} with data: {data}, received response: {response}")
                    return response
            else:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        raise Exception(f"Jira GET failed: {self.server.user}, {self.server.password}  url={url}\nstatus={resp.status}\nheaders={headers}\nbody={await resp.read()}")
                    response = await resp.json()
                    logging.info(f"Called external API with GET to {url}, received response: {response}")
                    return response


    def process_jira_response(self, response, resource_groups):
        issues = response.get('issues', [])
        processed_issues = []

        for issue in issues:
            fields = issue.get('fields', {})
            key = issue.get('key')
            summary = fields.get('summary')
            resolution = fields.get('resolution') is not None
            assignee = (fields.get('assignee', {}) or {}).get('displayName', '').replace('(External)', '(x)')
            processed_issue = parse_summary(resource_groups, summary)
            processed_issue.update({
                'key': key,
                'resolution': resolution,
                'assignee': assignee,
            })
            processed_issues.append(processed_issue)

        return {'issues': processed_issues}



def run(jira_server, port, token, user, password):
    # We accept only local connections to avoid creating a serious vulnerability.
    # Of course, a local malicious app still may access you Jira through the interface,
    # but that is still much better than opening access to remote hosts. :-)
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, RequestHandler)
    httpd.token = token
    httpd.user = user
    httpd.password = password
    httpd.jira_server = jira_server
    logging.info(f'Starting httpd server on port {port}')
    httpd.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Jira Driver for Twin Pigs Sprint Calculator v5.0')
    parser.add_argument('--port', type=int, default=8080, help='Specify the HTTP port to listen')
    parser.add_argument('--token', type=str, help='Jira API personal access token to use API (the recommended wat of authentication)')
    parser.add_argument('--user', type=str, help='Username for basic Jira API auth (kept for old Jira versions)')
    parser.add_argument('--password', type=str, help='Password for basic Jira API auth (kept for old Jira versions)')
    parser.add_argument('--jira', type=str, required=True, help='Jira server URL')
    args = parser.parse_args()
    if args.token:
        if args.user or args.password:
            print("You don't need --user and --password if you specify --token", file=sys.stderr)
            exit(1)
    else:
        if not (args.user and args.password):
            print("You need to specify --user and --password if you do not specify --token", file=sys.stderr)

    run(jira_server=args.jira, port=args.port, token=args.token, user=args.user, password=args.password)
