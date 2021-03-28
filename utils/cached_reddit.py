import os
import pickle
import random

import aiofiles
from asyncpraw import Reddit
from asyncpraw.models import Submission
from discord.ext import tasks
from typing import List

from config.reddit import reddit_config


class RedditPostCacher:
    def __init__(self, subreddit_names: List[str], cache_location):
        self.subreddit_names = subreddit_names

        # Asyncpraw client configuration
        self.reddit = Reddit(
            client_id=reddit_config.id,
            client_secret=reddit_config.secret,
            user_agent="Peace Bot",
        )

        # Determine the file name to save the caches to
        self.file_path = cache_location

    @tasks.loop(minutes=30)
    async def cache_posts(self):
        subreddits = [
            await self.reddit.subreddit(subreddit) for subreddit in self.subreddit_names
        ]
        data_to_dump = dict()
        for subreddit in subreddits:
            await subreddit.load()
            posts = [{'url': post.url, 'title': post.title} async for post in subreddit.hot(limit=50)]
            allowed_extensions = (".gif", ".png", ".jpg", ".jpeg")
            posts = list(
                filter(
                    lambda i: any((i.get('url').endswith(e) for e in allowed_extensions)),
                    posts,
                )
            )
            # print(post_urls[1:3])
            data_to_dump[subreddit.display_name] = posts


        async with aiofiles.open(self.file_path, mode="wb+") as f:
            await f.write(pickle.dumps(data_to_dump))

    async def get_random_post(self, subreddit: str) -> Submission:
        """Fetches a post from the internal cache

        Parameters
        ----------
        subreddit : str
            The name of the subreddit to fetch from

        Returns
        -------
        asyncpraw.models.Submission
            The randomly chosen submission

        Raises
        ------
        ValueError
            The subreddit was not in the internal cache
        """
        async with aiofiles.open(self.file_path, mode="rb") as f:
            cache = pickle.loads(await f.read())
            try:
                subreddit = cache[subreddit]
            except KeyError as e:
                raise ValueError("Subreddit not in cache!") from e
            else:
                random_post = random.choice(subreddit)
                return random_post
