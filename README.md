# Discord Predictions Bot 🎮

A Discord bot that allows you to run prediction challenges for match results (CS:GO, Dota 2, etc.) with a tournament system, rounds, and leaderboards.

## Features

- 🏆 **Tournaments**: Create tournaments with multiple rounds
- 📋 **Rounds**: Create standalone rounds or as part of a tournament
- 🎮 **Matches**: Add unlimited number of matches
- ✅ **Emoji Predictions**: Users make predictions using emoji reactions
- 🔒 **Close Predictions**: Admin can lock predictions before matches start
- 📊 **Dual Leaderboards**: Per round and overall tournament
- 👤 **Personal Stats**: Everyone can view their own predictions

## Installation

### 1. Requirements

- Python 3.8 or higher
- Discord bot token

### 2. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application (New Application)
3. Go to "Bot" section and click "Add Bot"
4. Enable the following Privileged Gateway Intents:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT
5. Copy the bot token

### 3. Invite Bot to Server

1. In Developer Portal, go to "OAuth2" → "URL Generator"
2. Select scopes:
   - `bot`
   - `applications.commands`
3. Select Bot Permissions:
   - Send Messages
   - Embed Links
   - Add Reactions
   - Read Message History
   - Use Slash Commands
4. Copy the generated URL and open it to add the bot to your server

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configuration

Create a `.env` file in the root folder:

```bash
cp .env.example .env
```

Edit `.env` and add your bot token:

```
DISCORD_TOKEN=your_token_here
```

### 6. Run the Bot

```bash
python bot.py
```

## How to Use

### For Admins

#### 1. Create Tournament (optional)

If you want to run a tournament with multiple rounds:

```
/create_tournament name:CS:GO Major 2024
```

The bot will give you a `tournament_id` - save it!

#### 2. Create Round

Create a round (part of tournament or standalone):

```
/create_round name:Quarterfinals tournament_id:tournament_123456_0
```

Or without tournament:

```
/create_round name:Match of the Day
```

The bot will give you a `round_id` - save it!

#### 3. Add Matches

```
/add_match round_id:round_123456_0 team1:Navi team2:Vitality
/add_match round_id:round_123456_0 team1:FaZe team2:G2
```

The bot will create messages with ✅ and ❌ reactions

#### 4. Users Make Predictions

Users react to match messages:
- ✅ = First team wins
- ❌ = Second team wins

#### 5. Close Predictions

Before matches start, close predictions:

```
/close_predictions round_id:round_123456_0
```

After this, new reactions won't be counted.

#### 6. Set Results

After each match, set the result:

```
/set_result round_id:round_123456_0 match_number:1 winner:Team 1
```

- `match_number` - sequential match number (starting from 1)
- `winner` - Team 1 or Team 2

#### 7. View Leaderboard

For a round:

```
/leaderboard round_id:round_123456_0
```

For a tournament:

```
/leaderboard tournament_id:tournament_123456_0
```

### For Users

#### View Your Predictions

```
/my_predictions round_id:round_123456_0
```

#### View Leaderboard

```
/leaderboard round_id:round_123456_0
```

or

```
/leaderboard tournament_id:tournament_123456_0
```

## Usage Example

### Scenario: CS:GO Major

1. Admin: `/create_tournament name:PGL Major Copenhagen 2024`
   - Gets: `tournament_guild_123_0`

2. Admin: `/create_round name:Playoffs Day 1 tournament_id:tournament_guild_123_0`
   - Gets: `round_guild_123_0`

3. Admin adds matches:
   ```
   /add_match round_id:round_guild_123_0 team1:Navi team2:Vitality
   /add_match round_id:round_guild_123_0 team1:FaZe team2:G2
   /add_match round_id:round_guild_123_0 team1:Liquid team2:Spirit
   ```

4. Users make predictions (react with ✅ or ❌)

5. Admin closes predictions: `/close_predictions round_id:round_guild_123_0`

6. Matches are played, admin sets results:
   ```
   /set_result round_id:round_guild_123_0 match_number:1 winner:Team 1
   /set_result round_id:round_guild_123_0 match_number:2 winner:Team 2
   /set_result round_id:round_guild_123_0 match_number:3 winner:Team 1
   ```

7. View round leaderboard:
   ```
   /leaderboard round_id:round_guild_123_0
   ```

8. Create next round and repeat the process

9. At the end of tournament, view overall leaderboard:
   ```
   /leaderboard tournament_id:tournament_guild_123_0
   ```

## Data Structure

All data is stored in the `data/` folder:

- `tournaments.json` - tournament and round information
- `predictions.json` - user predictions

## Commands

### Admin Commands

| Command | Description |
|---------|-------------|
| `/create_tournament` | Create a new tournament |
| `/create_round` | Create a round (in tournament or standalone) |
| `/add_match` | Add a match to a round |
| `/close_predictions` | Close predictions |
| `/set_result` | Set match result |
| `/leaderboard` | Show leaderboard |

### User Commands

| Command | Description |
|---------|-------------|
| `/my_predictions` | View your predictions |
| `/leaderboard` | Show leaderboard |
| `/help` | Show command help |

## Leaderboards

### Round Leaderboard

Shows results for one round:
- Number of correct predictions
- Success percentage
- Top 10 players

### Tournament Leaderboard

Shows overall results for all tournament rounds:
- Total correct predictions
- Overall success percentage
- Top 10 players for the entire tournament

## Troubleshooting

### Bot doesn't respond to commands

1. Check that the bot is online
2. Make sure slash commands are synced (restart the bot)
3. Check bot permissions on the server

### Reactions don't work

1. Make sure the bot has "Add Reactions" and "Read Message History" permissions
2. Check that predictions are open (`/close_predictions` wasn't called)

### Commands unavailable

1. Check that you have administrator permissions (for admin commands)
2. Restart the bot to sync commands

## Possible Improvements

- Automatic prediction closing by time
- Notifications for new matches
- Statistics per player
- Export leaderboard as image
- Points/rewards system
- Webhook integration with tournament APIs for automatic result updates

## License

MIT

## Support

If you encounter any issues, please create an issue in the project repository.
