# Discord-Bots

Discord-Gmail-Bot is an automation tool that retrieves messages from Gmail account, summarizes their content using `Gemini 2.0 Flash`, and sends notifications to `Discord` channel using `GitHub Actions`.

Currently, the bots are performining following actions:  
✅ PhD-Alerts: Collecting PhD Admissions messages  
🔜 Monetary Expenses: Analyzing spending patterns from transaction history 

## Requirements

- **Python**: Version 3.10
- **APIs & Credentials**:
  - Gmail API credentials ([OAuth2.0](https://console.cloud.google.com/apis/credentials/consent))
  - Gemini API access ([API key](https://ai.google.dev/gemini-api/docs/api-key))
  - Discord Bot token and Channel ID ([Developer Portal](https://discord.com/developers/docs/intro))
- **Additional Libraries**: Listed in the `requirements.txt` file.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/Discord-Bots.git
   cd Discord-Bots
   ```

2. **Create Virtual Environament**

    ```
    python3.10 -m venv venv
    source venv/bin/activate
    ```

3. **Install necessary dependencies:**

    ```
    pip install -r requirements.txt
    ```

4. **Generating `token.json`:**

    Make sure to setup new Project in the [Google Developer Console](https://console.developers.google.com/project) and enable `GMail API` and setup `OAuth2.0` credentials for **Desktop Application**. Once setup, you need to download the `credentials.json`. You can refer to the sample [here](https://github.com/pradhanhitesh/Discord-Bots/blob/main/SAMPLE/sample_credentials.json).

    Now, we need to generate the `token.json` file using `generate_tokens.py`. You need to authenticate once and generate neccessary fields for future authentication. You can refer to the sample token.json file [here](https://github.com/pradhanhitesh/Discord-Bots/blob/main/SAMPLE/sample_token.json). Further reading, please refer [here](https://developers.google.com/gmail/api/auth/web-server).

    ```
    python generate_tokens.py
    ```

5. **Set environment secrets:**

    ```
    GMAIL_TOKEN='your-token-json-file-here'
    GEMINI_API_KEY='your-key-here'
    DISCORD_BOT_TOKEN='your-token-here'
    DISCORD_CHANNEL_ID='your-channel-id-here'
    ```
