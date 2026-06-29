# velestra-reader

`velestra-reader` is a small, read-only local CLI helper for fetching public
Reddit content through Reddit's OAuth/Data API flow.

It is intended for personal, low-volume reading of public Reddit threads,
subreddit listings, and search results that the user manually requests. It does
not post, comment, vote, message users, moderate communities, automate account
activity, scrape Reddit HTML pages, store long-term datasets, resell data,
license data, target ads, or train AI/ML models.

## Capabilities

- Fetch a public Reddit thread and format the post/comment tree for local
  reading.
- Fetch public subreddit listings such as hot, new, top, rising, and
  controversial.
- Fetch public Reddit search results.
- Use OAuth requests against `https://oauth.reddit.com`.

## Non-Goals

- No posting, commenting, voting, messaging, moderation, or account automation.
- No browser-cookie reuse or login-session extraction.
- No HTML scraping fallback.
- No high-volume collection or dataset building.
- No resale, sublicensing, ad targeting, or model training use.

## Install

Requires Python 3.10+.

```bash
python3 -m pip install -e .
```

## Configure

Create a Reddit OAuth application using the app name `velestra-reader` and a
descriptive User-Agent such as:

```text
script:velestra-reader:0.1.0 (by /u/YOUR_REDDIT_USERNAME)
```

Then create a private local config file:

```bash
mkdir -p ~/.config/velestra-reader
chmod 700 ~/.config/velestra-reader
cp examples/config.env.example ~/.config/velestra-reader/config.env
chmod 600 ~/.config/velestra-reader/config.env
```

Edit `~/.config/velestra-reader/config.env` and fill in your approved Reddit
OAuth credentials:

```bash
VELESTRA_READER_AUTH=oauth
VELESTRA_READER_CLIENT_ID="your_client_id"
VELESTRA_READER_CLIENT_SECRET="your_client_secret"
VELESTRA_READER_USER_AGENT="script:velestra-reader:0.1.0 (by /u/YOUR_REDDIT_USERNAME)"
```

The CLI also supports `VELESTRA_READER_CONFIG=/path/to/config.env` and
`$XDG_CONFIG_HOME/velestra-reader/config.env`. Environment variables override
config-file values.

## Usage

Fetch and format a public thread:

```bash
velestra-reader thread "https://www.reddit.com/r/example/comments/abc/title/"
```

Fetch raw thread JSON:

```bash
velestra-reader thread --json "https://www.reddit.com/r/example/comments/abc/title/"
```

Fetch a subreddit listing:

```bash
velestra-reader subreddit Python --sort top --time week --limit 10
```

Search Reddit:

```bash
velestra-reader search "local llm tools" --subreddit LocalLLaMA --limit 10
```

## Data Handling

By default, output is written to stdout. If `--output` is supplied, output is
written to the path chosen by the user. The tool does not create a local Reddit
dataset, database, or background sync process.

OAuth credentials are read from the user's local config file or environment.
Secrets are not committed to this repository.

## Development

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py'
```
