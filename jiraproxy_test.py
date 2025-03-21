import unittest
import json
import asyncio
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from urllib.parse import urlparse
from aiohttp import ClientSession
from jiraproxy import RequestHandler, run

class FakeJiraHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/rest/api/2/search':
            self.handle_search()
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path.startswith('/rest/api/2/issue/'):
            self.handle_update(parsed_path.path.split('/')[-1])
        else:
            self.send_response(404)
            self.end_headers()

    def handle_search(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {'issues': [{'key': 'TEST-1', 'fields': {'assignee': {'displayName': 'Twin Pigs'}, 'resolution': {}, 'summary': 'A[5A+3B](2A+1B) Some description'}}]}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def handle_update(self, key):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        summary = data['fields']['summary']
        self.send_response(204)
        self.end_headers()
        logging.info(f"Updated issue {key} with summary: {summary}")

class TestRequestHandler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Running a fake Jira
        cls.jira_server = HTTPServer(('localhost', 8081), FakeJiraHandler)
        cls.jira_thread = Thread(target=cls.jira_server.serve_forever)
        cls.jira_thread.start()

        # Running a proxy to test
        cls.proxy_server = HTTPServer(('localhost', 8080), RequestHandler)
        cls.proxy_server.token = 'test_token'
        cls.proxy_server.jira_server = 'http://localhost:8081'
        cls.proxy_thread = Thread(target=cls.proxy_server.serve_forever)
        cls.proxy_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.proxy_server.shutdown()
        cls.proxy_thread.join()
        cls.jira_server.shutdown()
        cls.jira_thread.join()

    async def send_request(self, url, data):
        async with ClientSession() as session:
            async with session.post(url, json=data) as response:
                return await response.json()

    def test_post_query_issues(self):
        async def test():
            response = await self.send_request('http://localhost:8080/query_issues', {'jql': 'project=TEST', 'resource_groups': ['A', 'B']})
            self.assertIn('issues', response)
            self.assertEqual(response['issues'][0]['key'], 'TEST-1')
            self.assertEqual(response['issues'][0]['estimates'], {'A': 5, 'B': 3})
            self.assertEqual(response['issues'][0]['remaining_estimates'], {'A': 2, 'B': 1})
            self.assertEqual(response['issues'][0]['prefix'], 'A')
            self.assertEqual(response['issues'][0]['summary'], 'Some description')
            self.assertEqual(response['issues'][0]['assignee'], 'Twin Pigs')
            self.assertTrue(response['issues'][0]['resolution'])

        asyncio.run(test())

    def test_post_update_issues(self):
        async def test():
            response = await self.send_request('http://localhost:8080/update_issues', {
                'issues': [
                    {
                        'key': 'TEST-1',
                        'summary': 'Some description',
                        'prefix': 'A',
                        'estimates': {'A': 5, 'B': 3},
                        'remaining_estimates': {'A': 2, 'B': 2}  # Изменение оценки
                    }
                ],
                'jql': 'project=TEST'
            })
            self.assertIn('updated_keys', response)
            self.assertEqual(response['updated_keys'], ['TEST-1'])

        asyncio.run(test())

    def test_extract_estimates_and_clean_summary(self):
        handler = RequestHandler
        summary = 'A[5A+3B](2A+1B) Some description'
        resource_groups = ['A', 'B']
        estimates, remaining_estimates, prefix, cleaned_summary = handler.extract_estimates_and_clean_summary(handler, summary, resource_groups)
        self.assertEqual(estimates, {'A': 5, 'B': 3})
        self.assertEqual(remaining_estimates, {'A': 2, 'B': 1})
        self.assertEqual(prefix, 'A')
        self.assertEqual(cleaned_summary, 'Some description')

        summary = 'A[5A+3B]'
        estimates, remaining_estimates, prefix, cleaned_summary = handler.extract_estimates_and_clean_summary(handler, summary, resource_groups)
        self.assertEqual(estimates, {'A': 5, 'B': 3})
        self.assertEqual(remaining_estimates, {'A': 5, 'B': 3})
        self.assertEqual(prefix, 'A')
        self.assertEqual(cleaned_summary, '')

        summary = 'A[0](0)'
        estimates, remaining_estimates, prefix, cleaned_summary = handler.extract_estimates_and_clean_summary(handler, summary, resource_groups)
        self.assertEqual(estimates, {'A': 0, 'B': 0})
        self.assertEqual(remaining_estimates, {'A': 0, 'B': 0})
        self.assertEqual(prefix, 'A')
        self.assertEqual(cleaned_summary, '')

        summary = 'A[5A+3B] Some description'
        estimates, remaining_estimates, prefix, cleaned_summary = handler.extract_estimates_and_clean_summary(handler, summary, resource_groups)
        self.assertEqual(estimates, {'A': 5, 'B': 3})
        self.assertEqual(remaining_estimates, {'A': 5, 'B': 3})
        self.assertEqual(prefix, 'A')
        self.assertEqual(cleaned_summary, 'Some description')

        summary = 'A[5A+3B+2C](1A+1B+1C) Some description'
        resource_groups = ['A', 'B', 'C']
        estimates, remaining_estimates, prefix, cleaned_summary = handler.extract_estimates_and_clean_summary(handler, summary, resource_groups)
        self.assertEqual(estimates, {'A': 5, 'B': 3, 'C': 2})
        self.assertEqual(remaining_estimates, {'A': 1, 'B': 1, 'C': 1})
        self.assertEqual(prefix, 'A')
        self.assertEqual(cleaned_summary, 'Some description')

        summary = 'A[5A+3B] Some description (1A+1B)'
        estimates, remaining_estimates, prefix, cleaned_summary = handler.extract_estimates_and_clean_summary(handler, summary, ['A', 'B', 'C'])
        self.assertEqual(estimates, {'A': 5, 'B': 3, 'C': 0})
        self.assertEqual(remaining_estimates, {'A': 5, 'B': 3, 'C': 0})
        self.assertEqual(prefix, 'A')
        self.assertEqual(cleaned_summary, 'Some description (1A+1B)')

    def test_reconstruct_summary(self):
        handler = RequestHandler
        issue = {
            'key': 'TEST-1',
            'summary': 'Some description',
            'prefix': 'A',
            'estimates': {'A': 5, 'B': 3},
            'remaining_estimates': {'A': 2, 'B': 1}
        }
        summary = handler.reconstruct_summary(handler, issue)
        self.assertEqual(summary, 'A[5A+3B](2A+1B) Some description')

        handler = RequestHandler
        issue = {
            'key': 'TEST-1',
            'summary': 'Some description',
            'prefix': 'A',
            'estimates': {'A': 5, 'B': 3},
            'remaining_estimates': {'A': 5, 'B': 3}
        }
        summary = handler.reconstruct_summary(handler, issue)
        self.assertEqual(summary, 'A[5A+3B] Some description')

        issue = {
            'key': 'TEST-2',
            'summary': 'Another description',
            'prefix': 'B',
            'estimates': {'A': 0, 'B': 0},
            'remaining_estimates': {'A': 0, 'B': 0}
        }
        summary = handler.reconstruct_summary(handler, issue)
        self.assertEqual(summary, 'B[0] Another description')

if __name__ == '__main__':
    unittest.main()
