import requests
import random as r
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json
from discord import app_commands
from discord.ui import Select, View

############ CONFIG ###################
NOMBRE_EXTENSION = 6
NOMBRE_CARTES = 300
CHANNEL_ID = 1332686804113031249
#######################################


load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='&', intents=intents, case_insensitive=True)

def get_data(extension: str, carte: str) -> str:
    url = f'https://cdn.dreamborn.ink/images/fr/cards/{extension}-{carte}'
    response = requests.get(url)
    return url

async def send_card_message(channel_id):
    with open('output.json', 'r') as file:
        data = json.load(file)
    
    i = r.randint(0, len(data) - 1)
    extension = data[i]['extension']
    carte = data[i]['carte']
    url = get_data(extension, carte)
    
    embed = discord.Embed(title="Carte Dreamborn", color=0xd6bb8d)
    embed.set_image(url=url)    

    channel = channel_id
    if channel:
        try:
            print("(+) envoie du message")
            message = await channel.send(embed=embed)
            await message.add_reaction("1️⃣")
            await message.add_reaction("2️⃣")
            await message.add_reaction("3️⃣")
            await message.add_reaction("4️⃣")
            await message.add_reaction("5️⃣")
            print("(+) envoie ok")
        except Exception as e:
            print(f"(-) Erreur lors de l'envoi du message : {str(e)}")

@bot.tree.command(name="random", description="Renvoyer une carte aléatoire")
async def random(interaction: discord.Interaction):
    print("aléatoire trigger")
    with open('output.json', 'r') as file:
        data = json.load(file)
    
    i = r.randint(0, len(data) - 1)
    extension = data[i]['extension']
    carte = data[i]['carte']
    url = get_data(extension, carte)
    
    embed = discord.Embed(title="Carte Dreamborn", color=0xd6bb8d)
    embed.set_image(url=url)    

    try:
        print("(+) envoie du message")
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
        await message.add_reaction("3️⃣")
        await message.add_reaction("4️⃣")
        await message.add_reaction("5️⃣")
        print("(+) envoie ok")
    except Exception as e:
        print(f"(-) Erreur lors de l'envoi du message : {str(e)}")

class CardSelect(Select):
    def __init__(self, cards):
        options = []
        for card in cards:
            # Création des options du menu déroulant
            option = discord.SelectOption(
                label=f"{card['nom']}",
                description=f"{card['sous-nom']}",
                value=f"{card['extension']}-{card['carte']}"
            )
            options.append(option)
        
        super().__init__(
            placeholder="Sélectionnez une carte...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # Récupération de l'extension et du numéro de carte
        extension, carte = self.values[0].split('-')
        
        # Création de l'embed avec l'image
        image_url = f'https://cdn.dreamborn.ink/images/fr/cards/{extension}-{carte}'
        embed = discord.Embed(title="Carte Dreamborn", color=0xd6bb8d)
        embed.set_image(url=image_url)
        
        # Envoi de la réponse
        await interaction.response.send_message(embed=embed)

class CardView(View):
    def __init__(self, cards):
        super().__init__()
        self.add_item(CardSelect(cards))

@bot.tree.command(name="carte", description="Rechercher une carte Dreamborn")
@app_commands.describe(recherche="Nom ou sous-nom de la carte à rechercher")
async def carte(interaction: discord.Interaction, recherche: str):
    await interaction.response.defer()  # ← Déférer immédiatement la réponse
    print(f"Commande /carte reçue avec recherche: {recherche}")  # Debug
    
    # Conversion de la recherche en minuscules
    recherche = recherche.lower()
    resultat_carte = []

    try:
        # Lecture du fichier JSON
        with open("output.json", "r", encoding='utf-8') as file:
            print("Lecture du fichier JSON")  # Debug
            data = json.load(file)
            
            # Recherche des cartes correspondantes
            for card in data:
                if recherche in card['nom'].lower() or recherche in card['sous-nom'].lower():
                    resultat_carte.append(card)
                    print(f"Carte trouvée: {card['nom']}")  # Debug

        # Gestion des résultats
        if not resultat_carte:
            print("Aucune carte trouvée")  # Debug
            embed_no_carte = discord.Embed(
                title="Aucun résultat",
                description="Aucune carte n'a été trouvée pour cette recherche.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed_no_carte, ephemeral=True)
        else:
            print(f"Nombre de cartes trouvées: {len(resultat_carte)}")  # Debug
            # Limitation du nombre de résultats (maximum 25 options dans un Select)
            resultat_carte = resultat_carte[:25]
            
            # Création et envoi du menu de sélection
            view = CardView(resultat_carte)
            await interaction.followup.send(  # ← Utiliser followup au lieu de response.send_message
                "Sélectionnez une carte :",
                view=view,
                ephemeral=True
            )
    except Exception as e:
        print(f"Erreur lors de l'exécution de la commande: {str(e)}")  # Debug
        await interaction.followup.send(  # ← Utiliser followup ici aussi
            f"Une erreur s'est produite: {str(e)}",
            ephemeral=True
        )


@bot.event
async def on_ready():
    print(f'(+) {bot.user} has connected to Discord!')
    scheduler = AsyncIOScheduler()
    
    # Correction : passer la fonction comme référence sans l'exécuter
    scheduler.add_job(send_card_message, 'cron', args=[CHANNEL_ID], hour=9, minute=0)
    scheduler.start()
    
    try:
        synced = await bot.tree.sync()
        print(f"Synchronisé {len(synced)} commande(s)")
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes : {e}")

def main():
    token = os.getenv('DISCORD_TOKEN')
    if token is None:
        print("(-) Erreur : Le token Discord n'est pas défini dans le fichier .env.")
        return
    try:
        bot.run(token)
    except Exception as e:
        print(f"(+) Erreur lors du démarrage du bot : {str(e)}")

if __name__ == "__main__":
    main()