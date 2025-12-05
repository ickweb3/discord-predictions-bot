import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from data_manager import DataManager
from typing import Optional

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
dm = DataManager()

# Emoji for predictions
TEAM1_EMOJI = "✅"  # Checkmark for team1
TEAM2_EMOJI = "❌"  # X for team2

# Admin role check
def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.tree.command(name="create_tournament", description="[ADMIN] Create a new tournament")
@app_commands.describe(name="Tournament name")
@is_admin()
async def create_tournament(interaction: discord.Interaction, name: str):
    tournament_id = f"tournament_{interaction.guild.id}_{len(dm._load_json(dm.tournaments_file)['tournaments'])}"
    tournament = dm.create_tournament(tournament_id, name, interaction.guild.id)

    embed = discord.Embed(
        title="🏆 Tournament Created",
        description=f"**{name}**\nID: `{tournament_id}`",
        color=discord.Color.green()
    )
    embed.add_field(name="Info", value="Use `/create_round` to create rounds", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="create_round", description="[ADMIN] Create a new round")
@app_commands.describe(
    name="Round name",
    tournament_id="Tournament ID (leave empty for standalone round)"
)
@is_admin()
async def create_round(interaction: discord.Interaction, name: str, tournament_id: Optional[str] = None):
    round_id = f"round_{interaction.guild.id}_{len(dm._load_json(dm.tournaments_file)['rounds'])}"
    round_data = dm.create_round(round_id, name, interaction.guild.id, tournament_id)

    embed = discord.Embed(
        title="📋 Round Created",
        description=f"**{name}**\nID: `{round_id}`",
        color=discord.Color.blue()
    )

    if tournament_id:
        tournament = dm.get_tournament(tournament_id)
        if tournament:
            embed.add_field(name="Tournament", value=tournament["name"], inline=False)

    embed.add_field(name="Next Step", value="Use `/add_match` to add matches", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="add_match", description="[ADMIN] Add a match to the current round")
@app_commands.describe(
    round_id="Round ID",
    team1="First team name",
    team2="Second team name"
)
@is_admin()
async def add_match(interaction: discord.Interaction, round_id: str, team1: str, team2: str):
    try:
        match = dm.add_match(round_id, team1, team2)
        round_data = dm.get_round(round_id)

        if not round_data["predictions_open"]:
            await interaction.response.send_message("⚠️ Predictions are closed for this round!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎮 New Match",
            description=f"**{team1}** vs **{team2}**",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="How to predict?",
            value=f"{TEAM1_EMOJI} = {team1} wins\n{TEAM2_EMOJI} = {team2} wins",
            inline=False
        )
        embed.set_footer(text=f"Round: {round_data['name']} | Match ID: {match['id']}")

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        # Add reactions
        await message.add_reaction(TEAM1_EMOJI)
        await message.add_reaction(TEAM2_EMOJI)

        # Save message ID
        match_index = len(round_data["matches"]) - 1
        dm.set_match_message_id(round_id, match_index, message.id)

    except ValueError as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)


@bot.tree.command(name="close_predictions", description="[ADMIN] Close predictions for a round")
@app_commands.describe(round_id="Round ID")
@is_admin()
async def close_predictions(interaction: discord.Interaction, round_id: str):
    round_data = dm.get_round(round_id)
    if not round_data:
        await interaction.response.send_message("❌ Round not found", ephemeral=True)
        return

    dm.close_predictions(round_id)

    embed = discord.Embed(
        title="🔒 Predictions Closed",
        description=f"Round: **{round_data['name']}**\nNo new predictions will be accepted",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="set_result", description="[ADMIN] Set match result")
@app_commands.describe(
    round_id="Round ID",
    match_number="Match number (starting from 1)",
    winner="Winner (team1 or team2)"
)
@app_commands.choices(winner=[
    app_commands.Choice(name="Team 1", value="team1"),
    app_commands.Choice(name="Team 2", value="team2")
])
@is_admin()
async def set_result(interaction: discord.Interaction, round_id: str, match_number: int, winner: str):
    round_data = dm.get_round(round_id)
    if not round_data:
        await interaction.response.send_message("❌ Round not found", ephemeral=True)
        return

    match_index = match_number - 1
    if match_index < 0 or match_index >= len(round_data["matches"]):
        await interaction.response.send_message("❌ Invalid match number", ephemeral=True)
        return

    dm.set_match_result(round_id, match_index, winner)
    match = round_data["matches"][match_index]

    winner_name = match["team1"] if winner == "team1" else match["team2"]

    embed = discord.Embed(
        title="✅ Result Set",
        description=f"**{match['team1']}** vs **{match['team2']}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Winner", value=f"🏆 {winner_name}", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="my_predictions", description="View your predictions")
@app_commands.describe(round_id="Round ID")
async def my_predictions(interaction: discord.Interaction, round_id: str):
    round_data = dm.get_round(round_id)
    if not round_data:
        await interaction.response.send_message("❌ Round not found", ephemeral=True)
        return

    predictions = dm.get_user_predictions(round_id, interaction.user.id)

    if not predictions:
        await interaction.response.send_message("You don't have any predictions for this round yet", ephemeral=True)
        return

    embed = discord.Embed(
        title="📊 Your Predictions",
        description=f"Round: **{round_data['name']}**",
        color=discord.Color.blue()
    )

    for match in round_data["matches"]:
        match_id = match["id"]
        if match_id in predictions:
            prediction = predictions[match_id]
            predicted_team = match["team1"] if prediction == "team1" else match["team2"]

            result_emoji = ""
            if match["result"]:
                if match["result"] == prediction:
                    result_emoji = " ✅"
                else:
                    result_emoji = " ❌"

            embed.add_field(
                name=f"{match['team1']} vs {match['team2']}",
                value=f"Your prediction: **{predicted_team}**{result_emoji}",
                inline=False
            )

    # Add score if round is finished
    if round_data["predictions_open"] == False:
        leaderboard = dm.calculate_round_leaderboard(round_id)
        user_score = next((s for s in leaderboard if s["user_id"] == interaction.user.id), None)
        if user_score:
            embed.add_field(
                name="Your Score",
                value=f"{user_score['correct']}/{user_score['total']} ({user_score['percentage']}%)",
                inline=False
            )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="leaderboard", description="Show leaderboard")
@app_commands.describe(
    round_id="Round ID (for round leaderboard)",
    tournament_id="Tournament ID (for tournament leaderboard)"
)
async def leaderboard(interaction: discord.Interaction, round_id: Optional[str] = None, tournament_id: Optional[str] = None):
    if not round_id and not tournament_id:
        await interaction.response.send_message("❌ Specify round_id or tournament_id", ephemeral=True)
        return

    if round_id:
        round_data = dm.get_round(round_id)
        if not round_data:
            await interaction.response.send_message("❌ Round not found", ephemeral=True)
            return

        leaderboard_data = dm.calculate_round_leaderboard(round_id)

        embed = discord.Embed(
            title="🏆 Round Leaderboard",
            description=f"**{round_data['name']}**",
            color=discord.Color.gold()
        )

    else:  # tournament_id
        tournament = dm.get_tournament(tournament_id)
        if not tournament:
            await interaction.response.send_message("❌ Tournament not found", ephemeral=True)
            return

        leaderboard_data = dm.calculate_tournament_leaderboard(tournament_id)

        embed = discord.Embed(
            title="🏆 Tournament Leaderboard",
            description=f"**{tournament['name']}**",
            color=discord.Color.gold()
        )

    if not leaderboard_data:
        embed.add_field(name="Empty", value="No results yet", inline=False)
    else:
        leaderboard_text = ""
        for i, score in enumerate(leaderboard_data[:10], 1):  # Top 10
            user = await bot.fetch_user(score["user_id"])
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            leaderboard_text += f"{medal} **{user.name}**: {score['correct']}/{score['total']} ({score['percentage']}%)\n"

        embed.add_field(name="Top Players", value=leaderboard_text, inline=False)

    await interaction.response.send_message(embed=embed)


@bot.event
async def on_raw_reaction_add(payload):
    # Ignore bot's own reactions
    if payload.user_id == bot.user.id:
        return

    # Check if it's one of our prediction emojis
    if str(payload.emoji) not in [TEAM1_EMOJI, TEAM2_EMOJI]:
        return

    # Find the round and match
    all_data = dm._load_json(dm.tournaments_file)
    round_id = None
    match_data = None
    match_index = None

    for rid, round_info in all_data["rounds"].items():
        for idx, match in enumerate(round_info["matches"]):
            if match["message_id"] == payload.message_id:
                round_id = rid
                match_data = match
                match_index = idx
                break
        if round_id:
            break

    if not round_id or not match_data:
        return

    # Check if predictions are still open
    round_data = dm.get_round(round_id)
    if not round_data["predictions_open"]:
        # Remove reaction if predictions are closed
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = await bot.fetch_user(payload.user_id)
        await message.remove_reaction(payload.emoji, user)
        return

    # Determine prediction
    prediction = "team1" if str(payload.emoji) == TEAM1_EMOJI else "team2"

    # Save prediction
    dm.save_prediction(round_id, match_data["id"], payload.user_id, prediction)

    # Remove the opposite reaction if user already reacted
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = await bot.fetch_user(payload.user_id)

    opposite_emoji = TEAM2_EMOJI if prediction == "team1" else TEAM1_EMOJI
    await message.remove_reaction(opposite_emoji, user)


@bot.tree.command(name="help", description="Show help for commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Prediction Bot Help",
        description="Bot for predicting match results with tournaments and rounds",
        color=discord.Color.blue()
    )

    admin_commands = """
    `/create_tournament` - Create a tournament
    `/create_round` - Create a round (part of tournament or standalone)
    `/add_match` - Add a match to a round
    `/close_predictions` - Close predictions
    `/set_result` - Set match result
    `/leaderboard` - Show leaderboard
    """

    user_commands = """
    `/my_predictions` - View your predictions
    `/leaderboard` - Show leaderboard
    React to match messages to make predictions
    """

    embed.add_field(name="👑 Admin Commands", value=admin_commands, inline=False)
    embed.add_field(name="👤 User Commands", value=user_commands, inline=False)
    embed.add_field(
        name="ℹ️ How it works",
        value="1. Admin creates tournament or round\n2. Admin adds matches\n3. Users react (✅/❌) to predict\n4. Admin closes predictions\n5. Admin sets results\n6. System calculates leaderboard",
        inline=False
    )

    await interaction.response.send_message(embed=embed)


# Run the bot
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not found in .env file")
    else:
        bot.run(token)
