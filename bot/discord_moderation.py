from os import getenv
from discord import Intents
from discord import Message
from discord.ext.commands import Bot, Context
from dotenv import load_dotenv
import aiohttp
from discord import Interaction
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage
from langchain_core.prompts import SystemMessagePromptTemplate

load_dotenv()

intents = Intents.all()
bot = Bot(command_prefix="!", intents=intents)
llm = ChatOllama(model="llama3.2:1b")
API_BASE_URL = "http://localhost:8000"

systeme_message ="Tu es un assistant IA qui permet de modérer les discussions. **NE DEPASSE JAMAIS 1500 CHARACTERES**"

@bot.event
async def on_ready():
    await bot.tree.sync()
    channel = bot.get_channel(1362336418633875502)
    await channel.send("[NexaBot]: Prêt à vous modérer !")


@bot.tree.command(name="ban", description="Ajouter un sujet à bannir")
async def ban_command(interaction: Interaction, topic: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE_URL}/ban_topics", json={"topic": topic}) as resp:
            if resp.status == 200:
                await interaction.response.send_message(f"✅ Sujet **{topic}** banni.")
            else:
                await interaction.response.send_message("❌ Erreur lors de l'ajout du sujet.", ephemeral=True)

@bot.tree.command(name="unban", description="Supprimer un sujet banni")
async def unban_command(interaction: Interaction, topic: str):
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{API_BASE_URL}/ban_topics", json={"topic": topic}) as resp:
            if resp.status == 200:
                await interaction.response.send_message(f"✅ Sujet **{topic}** retiré.")
            else:
                await interaction.response.send_message("❌ Erreur lors de la suppression du sujet.", ephemeral=True)

@bot.tree.command(name="rules", description="Afficher les sujets bannis")
async def rules_command(interaction: Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE_URL}/rules") as resp:
            if resp.status == 200:
                rules = await resp.json()
                banned_topics = rules.get("banned_topics", [])
                if banned_topics:
                    await interaction.response.send_message("📌 Sujets bannis : " + ", ".join(banned_topics))
                else:
                    await interaction.response.send_message("✅ Aucun sujet banni pour le moment.")
            else:
                await interaction.response.send_message("❌ Impossible de récupérer les règles.", ephemeral=True)

@bot.event
async def on_message(message: Message):
    if message.author.bot:
        return

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/rules") as resp:
                if resp.status != 200:
                    print("[Erreur API] Impossible d'obtenir les règles.")
                    return
                rules = await resp.json()
                banned_topics = rules.get("banned_topics", [])
                print(f"[Règles récupérées] {banned_topics}")

        except Exception as e:
            print(f"[Erreur récupération des règles] {e}")
            return

    if not banned_topics:
        return  

    banned_list = ", ".join(banned_topics)
    prompt_text = (
        "Tu es un assistant de modération. "
        "Dis uniquement OUI ou NON. "
        f"Est-ce que le message parle de l’un de ces sujets interdits : {banned_list} ?"
    )

    systeme_prompt = SystemMessagePromptTemplate.from_template(prompt_text)

    context = [
        systeme_prompt.format(),
        HumanMessage(message.content)
    ]

    try:
        ai_message = await llm.ainvoke(context)
        response_text = ai_message.content.strip().lower()

        if "oui" in response_text:
            print(f"[Message banni] {message.content}")
            await message.delete()
            try:
                await message.author.send(
                    f"⚠️ Ton message a été supprimé car il contient un sujet interdit : **{banned_list}**."
                )
            except:
                print("Impossible d’envoyer un message privé à l’utilisateur.")
        else:
            print(f"[Message clean] {message.content}")
            return  # Le message est clean
        

    except Exception as e:
        print(f"[Erreur IA LangChain] {e}")


bot.run(getenv("TOKEN"))