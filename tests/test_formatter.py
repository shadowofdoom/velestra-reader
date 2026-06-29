import unittest

from velestra_reader.formatter import format_thread


class TestFormatThread(unittest.TestCase):
    def test_formats_post_and_nested_comments(self):
        payload = [
            {
                "kind": "Listing",
                "data": {
                    "children": [
                        {
                            "kind": "t3",
                            "data": {
                                "title": "A useful thread",
                                "author": "poster",
                                "score": 42,
                                "num_comments": 2,
                                "selftext": "Original post body",
                                "permalink": "/r/example/comments/abc/a_useful_thread/",
                            },
                        }
                    ]
                },
            },
            {
                "kind": "Listing",
                "data": {
                    "children": [
                        {
                            "kind": "t1",
                            "data": {
                                "author": "commenter",
                                "score": 7,
                                "body": "First comment",
                                "replies": {
                                    "kind": "Listing",
                                    "data": {
                                        "children": [
                                            {
                                                "kind": "t1",
                                                "data": {
                                                    "author": "reply",
                                                    "score": 3,
                                                    "body": "Nested reply",
                                                    "replies": "",
                                                },
                                            }
                                        ]
                                    },
                                },
                            },
                        }
                    ]
                },
            },
        ]

        result = format_thread(payload)

        self.assertIn("Title: A useful thread", result)
        self.assertIn("Author: poster", result)
        self.assertIn("Comments: 2", result)
        self.assertIn("- commenter (score: 7): First comment", result)
        self.assertIn("  - reply (score: 3): Nested reply", result)


if __name__ == "__main__":
    unittest.main()
