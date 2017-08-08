# # Copyright (c) 2017 ellesde
# # 
# # This software is released under the MIT License.
# # https://opensource.org/licenses/MIT

import discord
from discord.ext import commands
import os
from cogs.utils.dataIO import dataIO
from cogs.utils.chat_formatting import box
import asyncio
import aiohttp

try: # check if BeautifulSoup4 is installed
    from bs4 import BeautifulSoup
    soupAvailable = True
except:
    soupAvailable = False

class Limimin:
    """Limimin related commands"""
    base_dir = os.path.join("data", "limimin")
    terms_path = os.path.join(base_dir, "terms.json")
    stamp_format = "Stamp_0{}_Icon.png"

    def __init__(self, bot):
        self.bot = bot
        self.base_dir = Limimin.base_dir
        self.stamp_format = Limimin.stamp_format
        self.terms_path = Limimin.terms_path
        self.terms = dataIO.load_json(self.terms_path)
        self.size = "sm"

    def _add_term(self, server, term, id):
        terms = {}

        if server.id not in self.terms:
            self.terms[server.id] = terms
        else:
            terms = self.terms[server.id]
        
        terms[term] = self.stamp_format.format(id)
        self.terms[server.id] = terms
        self._save_terms()

    def _del_term(self, server, term):
        self.terms[server.id].pop(term)
        self._save_terms()

    def _save_terms(self):
        dataIO.save_json(self.terms_path, self.terms)

    def _term_exists(self, server, term):
        if server.id not in self.terms:
            return False

        terms = self.terms[server.id] 
        return term in terms

    def _valid_id(self, id):
        # stamp id ranges from 19 to 39
        return id >= 19 and id <= 39

    def _valid_term(self, term):
        for char in term:
            if char.isdigit() or char.isalpha():
                pass
            else:
                return False
        
        return True

    @commands.group(pass_context=True, no_pm=True, name="limiset")
    async def limiset(self, ctx):
        """Limimin settings"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @limiset.command(pass_context=True, np_pm=True, name="add")
    async def limiset_add(self, ctx, term, id: int):
        """Add a term for a limimin stamp
        
        Stamp ids can be found at unisonleague.wikia.com/wiki/Stamps

        Example: !limiset add hello 26
        """
        server = ctx.message.server

        if not self._valid_id(id):
            await self.bot.say("That id is invalid. It must be between 19 and 39.")
            return

        if not self._valid_term(term):
            await self.bot.say("That term is invalid. It must only contain" +
            " alpha-numeric characters.")
            return

        if self._term_exists(server, term):
            await self.bot.say("That term is already is in use.")
            return

        self._add_term(server, term, id)
        await self.bot.say("{} assigned to {}.".format(self.stamp_format.format(id), term))

    @limiset.command(pass_context=True, np_pm=True, name="del")
    async def limiset_del(self, ctx, term):
        """Deletes a term"""
        server = ctx.message.server

        if not self._valid_term(term):
            await self.bot.say("That term is invalid. It must only contain" +
            " alpha-numeric characters.")
            return

        if not self._term_exists(server, term):
            await self.bot.say("That term does not exist.")
            return

        self._del_term(server, term)
        await self.bot.say("Term {} deleted".format(term))
        
    @limiset.command(pass_context=True, np_pm=True, name="list")
    async def limiset_list(self, ctx):
        """Lists available terms"""
        server = ctx.message.server

        message = "Term list:\n"
        if server.id in self.terms:
            terms = self.terms[server.id]
            for term in sorted(terms):
                message += "\t{}\n".format(term)
        
        await self.bot.say(box(message))

    @limiset.command(np_pm=True, name="size")
    async def limiset_size(self):
        """Toggle size of limimin stamps"""
        if self.size == "sm":
            self.size = "lg"
            await self.bot.say("Limimin stamp size set to large.")
            return
        else:
            self.size = "sm"
            await self.bot.say("Limimin stamp size set to small.")
            return

    @commands.command(pass_context=True, np_pm=True, name="limi")
    async def limi(self, ctx, term):
        """Send a limimin stamp to channel"""
        server = ctx.message.server

        if not self._term_exists(server, term):
            await self.bot.say("That term does not exist.")
            return

        message = ctx.message
        image_name = self.terms[server.id][term]
        image_path = "{}/{}/{}".format(self.base_dir, self.size, image_name)
        await self.bot.send_file(message.channel, image_path)
    
def check_folders():
    # create data/limimin/sm if not there
    sm = "{}/{}".format(Limimin.base_dir, "sm")
    if not os.path.exists(sm):
        print("Creating {} folder...".format(sm))
        os.makedirs(sm)

    # create data/limimin/lg if not there
    lg = "{}/{}".format(Limimin.base_dir, "lg")
    if not os.path.exists(lg):
        print("Create {} folder...".format(lg))
        os.makedirs(lg)

def check_files():
    # create data/terms.json if not there
    default = {}

    if not os.path.isfile(Limimin.terms_path):
        print("Creating default terms.json...")
        dataIO.save_json(Limimin.terms_path, default)

async def check_stamps(size):
    # download  limimin stamps if not there
    async with aiohttp.ClientSession() as session:
        stamp_url = "http://unisonleague.wikia.com/wiki/Stamps"
        async with session.get(stamp_url) as response:
            soup = BeautifulSoup(await response.text(), "html.parser")

        # stamp id ranges from 19 to 39
        for x in range(19, 39):
            image_name = Limimin.stamp_format.format(x)
            try:
                image_path = "{}/{}/{}".format(Limimin.base_dir, size, image_name)
                image_url = soup.find("img", attrs={"data-image-key": image_name})["src"]

                if size == "lg":
                    image_url = image_url.replace("/scale-to-width-down/80", "")

                if not os.path.exists(image_path):
                    print("Downloading from {}...".format(image_url))
                    async with session.get(image_url) as r:
                        image = await r.content.read()
                    with open(image_path, "wb") as f:
                        f.write(image)
            except Exception as e:
                print(e)
        return

def setup(bot):
    # check for beautifulSoup4
    if not soupAvailable:
        raise RuntimeError("You need to run `pip3 install beautifulsoup4`")

    # main
    check_folders()
    check_files()
    bot.add_cog(Limimin(bot))
    bot.loop.create_task(check_stamps("sm"))
    bot.loop.create_task(check_stamps("lg"))