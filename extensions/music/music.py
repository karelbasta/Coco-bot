"""Music bot commands cog module"""
import math
from typing import Optional

import discord
from discord.ext import commands
from core.basecog import BaseCog

from .voicestate import VoiceState
from .ytdlsource import YTDLError


async def _is_playing(ctx: commands.Context) -> bool:
    """Check if the bot is playing"""
    if ctx.voice_state.is_playing():
        return True
    await ctx.send("Nothing is playing.")
    return False


class Music(BaseCog):
    """Music bot commands cog"""

    def __init__(self, bot) -> None:
        """Music class init with dictionary for voice states"""
        super().__init__(bot)
        self.voice_states = {}

    def _get_voice_state(self, ctx) -> VoiceState:
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state
        return state

    def cog_check(self, ctx: commands.Context) -> bool:
        """Check if the user is in a voice channel"""
        if ctx.author.voice is None:
            ctx.send("Stop bothering me, when you are not in a voice channel.")
            return False
        return True

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        """Get voice state before commad invocation"""
        ctx = await super().cog_before_invoke(ctx)
        ctx.voice_state = self._get_voice_state(ctx)

    @commands.command(
        name="join", invoke_without_subcommand=True, aliases=["summon", "connect"]
    )
    async def _join(
        self, ctx: commands.Context, *, channel: discord.VoiceChannel = None
    ) -> None:
        """Summon the bot to a voice channel"""
        if not channel and not ctx.author.voice:
            await ctx.send("Stop bothering me, when you are not in a voice channel.")
            return
        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.move_to(destination)
            return
        await ctx.voice_state.connect(destination)

    @commands.command(name="leave", aliases=["disconnect", "dc"])
    async def leave(self, ctx: commands.Context) -> None:
        """Disconnect from the voice channel"""
        if not ctx.voice_state.voice:
            return await ctx.send("I am not in a voice channel.")
        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        """Play a song by query or link"""
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)
        async with ctx.typing():
            try:
                song = await ctx.voice_state.add_song(query)
            except YTDLError as err:
                return await ctx.send(
                    f"An error occurred while processing this request: {str(err)}"
                )
            await ctx.send("Enqued:", embed=song.make_song_embed())

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context) -> None:
        """Stop playing and clear the queue"""
        if await _is_playing(ctx):
            await ctx.voice_state.stop()
            return await ctx.message.add_reaction("⏹")

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context) -> None:
        """Pause the currently playing song"""
        if await _is_playing(ctx):
            if ctx.voice_state.is_paused():
                return await ctx.send("Already paused.")
            ctx.voice_state.pause()
            await ctx.message.add_reaction("⏸")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context) -> None:
        """Resume the currently paused song"""
        if await _is_playing(ctx):
            if not ctx.voice_state.is_paused():
                return await ctx.send("Not paused.")
            ctx.voice_state.resume()
            await ctx.message.add_reaction("▶️")

    @commands.command(name="now", aliases=["current", "playing"])
    async def now(self, ctx: commands.Context) -> None:
        """Display the currently playing song"""
        if await _is_playing(ctx):
            await ctx.send(embed=ctx.voice_state.current.make_song_embed())

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context) -> None:
        """Skip the currently playing song"""
        if await _is_playing(ctx):
            ctx.voice_state.skip()
            await ctx.message.add_reaction("⏭")

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx: commands.Context, *, page: int = 1) -> None:
        """Show the player's queue"""
        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("Empty queue")
        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ""
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += f"`{i + 1}.` [**{song.title}**]({song.url})\n"

        embed = discord.Embed(description=queue, color=0x00FF00)
        embed.set_footer(text=f"Viewing page {page}/{pages}")
        await ctx.send(embed=embed)

    @commands.command(name="remove", aliases=["r"])
    async def remove(self, ctx: commands.Context, index: int) -> None:
        """Remove a song from the queue"""
        try:
            ctx.voice_state.songs.remove(index - 1)
            await ctx.message.add_reaction("✅")
        except IndexError:
            return await ctx.send("Invalid position.")

    @commands.command(name="volume", aliases=["vol"])
    async def volume(self, ctx: commands.Context, volume: Optional[int] = None) -> None:
        """Change the player's volume"""
        if await _is_playing(ctx):
            if volume is None:
                return await ctx.send(f"Volume is {ctx.voice_state.volume*100}%")
            if 0 <= volume <= 200:
                ctx.voice_state.volume = volume / 100
                return await ctx.send(f"Volume is {ctx.voice_state.volume*100}%")
            await ctx.send("Volume must be between 0 and 200 %")

    @commands.command(name="loop")
    async def loop(self, ctx: commands.Context) -> None:
        """Loop the currently playing song"""
        if await _is_playing(ctx):
            ctx.voice_state.loop = not ctx.voice_state.loop
            negative = "" if ctx.voice_state.loop else "not "
            await ctx.send(f"Song will now {negative}loop.")

    @commands.command(name="shuffle")
    async def shuffle(self, ctx: commands.Context) -> None:
        """Shuffle the queue"""
        if len(ctx.voice_state.songs) <= 1:
            return await ctx.send("Not enough songs in queue")
        ctx.voice_state.shuffle()
        await ctx.message.add_reaction("🔀")
