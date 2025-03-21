import asyncio
import json
import argparse
import re
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode
import aiohttp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
        if not issues or not jql:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing issues or jql parameter'}).encode('utf-8'))
            return

        input_summaries = {issue['key']: self.reconstruct_summary(issue) for issue in issues}

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

    async def update_jira_summary(self, key, summary):
        jira_url = f'{self.server.jira_server}/rest/api/2/issue/{key}'
        data = {
            'fields': {
                'summary': summary
            }
        }
        headers = {
            'Authorization': f'Bearer {self.server.token}',
            'Content-Type': 'application/json'
        }
        async with aiohttp.ClientSession() as session:
            async with session.put(jira_url, json=data, headers=headers) as resp:
                if resp.status != 204:
                    logging.error(f"Failed to update summary for {key}: {resp.status}")

    async def call_external_api(self, url, data=None):
        headers = {
            'Authorization': f'Bearer {self.server.token}',
            'Content-Type': 'application/json'
        }
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
                        raise Exception("Jira GET failed")
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
            estimates, remaining_estimates, prefix, cleaned_summary = self.extract_estimates_and_clean_summary(summary,
                                                                                                               resource_groups)
            processed_issue = {
                'key': key,
                'summary': cleaned_summary,
                'prefix': prefix,
                'estimates': estimates,
                'remaining_estimates': remaining_estimates,
                'resolution': resolution,
                'assignee': assignee,
            }
            processed_issues.append(processed_issue)

        return {'issues': processed_issues}

    def extract_estimates_and_clean_summary(self, summary, resource_groups):
        estimates = {group: 0 for group in resource_groups}
        remaining_estimates = {group: 0 for group in resource_groups}
        prefix = ''
        cleaned_summary = summary.strip()

        if summary:
            # Extracting the estimates in square brackets
            match_square = re.search(r'^([^\[]{0,3}?)\[([^\]]+)\]', summary)
            match_round = None
            if match_square:
                prefix = match_square.group(1).strip()
                estimates_block = match_square.group(2).replace(' ', '')
                if estimates_block != '0':
                    # A regex to extract <Number><Letter> estimates
                    estimates_matches = re.findall(r'(\d+)([A-Za-z])', estimates_block)
                    for value, group in estimates_matches:
                        if group in resource_groups:
                            estimates[group] = int(value)

                # The round brackets immediately after the square brackets
                remaining_estimates_start = match_square.end()
                if remaining_estimates_start < len(summary) and summary[remaining_estimates_start] == '(':
                    match_round = re.search(r'\(([^\)]+)\)', summary[remaining_estimates_start:])
                    if match_round:
                        remaining_estimates_block = match_round.group(1).replace(' ', '')
                        if remaining_estimates_block != '0':
                            remaining_estimates_matches = re.findall(r'(\d+)([A-Za-z])', remaining_estimates_block)
                            for value, group in remaining_estimates_matches:
                                if group in resource_groups:
                                    remaining_estimates[group] = int(value)
                    else:
                        # If the round brackets are missing, we copy the original estimates
                        remaining_estimates = estimates.copy()
                else:
                    # If the round brackets are missing, we copy the original estimates
                    remaining_estimates = estimates.copy()

                # Extracting the clean summary with no extra data
                cleaned_summary = summary[match_square.end():].strip()
                if match_round:
                    cleaned_summary = summary[remaining_estimates_start + len(match_round.group(0)):].strip()

        return estimates, remaining_estimates, prefix, cleaned_summary

    def reconstruct_summary(self, issue):
        prefix = issue.get('prefix', '')
        estimates = issue.get('estimates', {})
        remaining_estimates = issue.get('remaining_estimates', {})
        summary = issue.get('summary', '')

        estimates_str = '+'.join(f'{value}{key}' for key, value in estimates.items() if value > 0)
        remaining_estimates_str = '+'.join(f'{value}{key}' for key, value in remaining_estimates.items() if value > 0)

        if not remaining_estimates_str and estimates_str:
            remaining_estimates_str = '(0)'
        else:
            if remaining_estimates_str == estimates_str:
                remaining_estimates_str = ''
            else:
                remaining_estimates_str = f'({remaining_estimates_str})'

        if not estimates_str:
            estimates_str = '[0]'
        else:
            estimates_str = f'[{estimates_str}]'

        return f'{prefix}{estimates_str}{remaining_estimates_str} {summary}'.strip()


def run(jira_server, port, token):
    # We accept only local connections to avoid creating a serious vulnerability.
    # Of course, a local malicious app still may access you Jira through the interface,
    # but that is still much better than opening access to remote hosts. :-)
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, RequestHandler)
    httpd.token = token
    httpd.jira_server = jira_server
    logging.info(f'Starting httpd server on port {port}')
    httpd.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Jira Proxy for Twin Pigs Jira Integrator v4')
    parser.add_argument('--port', type=int, default=8080, help='Specify the HTTP port to listen')
    parser.add_argument('--token', type=str, required=True, help='Jira API personal access token to use API')
    parser.add_argument('--jira', type=str, required=True, help='Jira server URL')
    args = parser.parse_args()

    run(jira_server=args.jira, port=args.port, token=args.token)
