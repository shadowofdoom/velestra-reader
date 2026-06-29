import unittest

from velestra_reader.client import (
    build_search_path,
    build_subreddit_listing_path,
    build_thread_path,
    oauth_url_for_reddit_url,
)


class TestOAuthUrls(unittest.TestCase):
    def test_converts_reddit_json_url_to_oauth_endpoint(self):
        result = oauth_url_for_reddit_url(
            "https://www.reddit.com/r/python/comments/abc/title.json?limit=10"
        )

        self.assertEqual(
            result,
            "https://oauth.reddit.com/r/python/comments/abc/title?limit=10",
        )

    def test_converts_reddit_path_to_oauth_endpoint(self):
        result = oauth_url_for_reddit_url("/r/python/hot?limit=5")

        self.assertEqual(result, "https://oauth.reddit.com/r/python/hot?limit=5")

    def test_rejects_non_reddit_url(self):
        with self.assertRaises(ValueError):
            oauth_url_for_reddit_url("https://example.com/r/python/hot.json")


class TestBuildPaths(unittest.TestCase):
    def test_builds_thread_path_for_public_thread_url(self):
        result = build_thread_path(
            "https://www.reddit.com/r/codex/comments/abc/title/?sort=new#frag"
        )

        self.assertEqual(
            result,
            "/r/codex/comments/abc/title?limit=500&depth=10&raw_json=1",
        )

    def test_builds_subreddit_listing_path(self):
        result = build_subreddit_listing_path("Python", sort="top", time="week", limit=10)

        self.assertEqual(result, "/r/Python/top?limit=10&t=week&raw_json=1")

    def test_builds_search_path(self):
        result = build_search_path(
            "codex reddit reader",
            subreddit="LocalLLaMA",
            sort="relevance",
            time="month",
            limit=25,
        )

        self.assertEqual(
            result,
            "/r/LocalLLaMA/search?q=codex+reddit+reader&restrict_sr=on&sort=relevance&t=month&limit=25&raw_json=1",
        )


if __name__ == "__main__":
    unittest.main()
