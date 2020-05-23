# MIT License
# Copyright (c) 2019-2020 Fyssion
# See LICENSE for license details

from discord.ext import commands
import discord

import re
from .utils.utils import (
    wait_for_deletion,
    check_for_help,
    is_opted_out,
    add_to_statistics,
)


class Subreddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.log
        self.reddit = self.bot.reddit

    def isWoshDetector(self, sub):
        """
        My solution for people linking 'wosh' (or any other varient of 'woooosh')
        Returns a message linking to the actual woooosh subreddit if a user tries to link to a varient.
        """
        if (
            sub == "whosh"
            or sub == "wosh"
            or sub == "whoosh"
            or sub == "whooosh"
            or sub == "woosh"
            or sub == "wooosh"
            or "oooo" in sub
            or "wosh" in sub
            or "whosh" in sub
            and sub != "woooosh"
        ):
            if sub != "woooosh":
                return "\n\nLooking for [r/woooosh](https://reddit.com/r/woooosh)?"
        return ""

    def regex_subreddit(self, message):
        args = message.split("r/")
        afterSlash = " ".join(args[1:])
        args = afterSlash.split(" ")
        sub = " ".join(args[0:1])

        sub = re.sub(
            """[!\.\?\-\'\"\*]""", "", sub
        )  # Replaces listed characters with a blank

        return sub

    def subreddit_link_detector(self, message):
        """Extremely simple algorithm that detects if 'r/' was found in a message and finds the text directly after."""

        urls = re.findall(
            "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            message,
        )  # Finds all urls in the message

        # If the message has any urls, the bot doesnt relink the subreddit
        if len(urls) > 0:
            return

        if message.startswith("r/") or message.startswith("/r/"):
            return self.regex_subreddit(message)

        if " r/" in message or " /r/" in message:
            return self.regex_subreddit(message)

    async def display_subreddit(self, message, subreddit):
        """
        Basically fetches the subreddit, creates the embed, and sends it.
        """

        if subreddit.over18 == True:
            isNSFW = "\n:warning:Subreddit is NSFW!:warning:"
        else:
            isNSFW = ""

        description = f"[r/{subreddit.display_name}](https://reddit.com/r/{subreddit.display_name})\
            \n{subreddit.public_description}{isNSFW}{self.ifIsWosh}{check_for_help(subreddit.display_name) or ''}"

        description += "\n\n" + self.bot.optout_message

        em_url = f"https://reddit.com/r/{subreddit.display_name}"

        em = discord.Embed(
            title=subreddit.title,
            description=description,
            url=em_url,
            color=self.bot.reddit_color,
        )

        em.add_field(name="Subscribers:", value=str(subreddit.subscribers))

        # The next if/else statements are a bug patch. Sometimes, subreddit.icon_img returns None instead of a blank string.
        # Disocrd will not accept this as a url, so I change None to a blank string
        if not subreddit.icon_img:
            subIcon = ""
        else:
            subIcon = subreddit.icon_img

        em.set_thumbnail(url=subIcon)
        em.set_footer(text=self.bot.auto_deletion_message)

        bot_message = await message.channel.send(embed=em)
        self.bot.loop.create_task(
            wait_for_deletion(
                bot_message, user_ids=(message.author.id,), client=self.bot
            )
        )

    async def subreddit_not_found(self, message, sub):
        """
        Sends an embed saying the subreddit does not exist.
        """

        msg = f":warning: Subreddit `{sub}` does not exist.{self.ifIsWosh}{check_for_help(sub) or ''}"

        msg += "\n\n" + self.bot.optout_message

        em = discord.Embed(description=msg, color=self.bot.warning_color)

        await message.channel.send(embed=em, delete_after=7)

    @commands.Cog.listener("on_message")
    async def on_subreddit(self, message):
        if is_opted_out(message.author, self.bot):
            return

        sub = self.subreddit_link_detector(message.content)

        if sub is not None:

            self.log.info(str(message.author) + " tried to link to '" + sub + "'")

            self.ifIsWosh = self.isWoshDetector(sub)

            # Searching for subreddit to see if it exists
            subreddit = await self.reddit.fetch_subreddit(sub)

            add_to_statistics(self.bot, "subreddit")

            if subreddit:
                await self.display_subreddit(message, subreddit)

            else:
                await self.subreddit_not_found(message, sub)


def setup(bot):
    bot.add_cog(Subreddit(bot))
