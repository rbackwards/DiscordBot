import os
import discord
import asyncio
from openai import OpenAI
from discord.ext import commands
from rich import print
import tiktoken
import time
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

ELEVENLABSTOKEN = os.getenv('ELEVEN_LABS')
client = ElevenLabs(api_key=ELEVENLABSTOKEN,)

TOKEN = os.getenv('DISCORD_TOKEN')
ELEVENLABS_TOKEN = os.getenv('ELEVEN_LABS')
intents1=discord.Intents.default()
intents1.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents1)

def text_to_speech_file(text: str) -> str:
    # Calling the text_to_speech conversion API with detailed parameters
    response = client.text_to_speech.convert(
        voice_id="9fkMM2aAuc1g9tO4pxf8", # testing
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.5,
            style=0.5,
            use_speaker_boost=True,
        ),
    )
    
    # uncomment the line below to play the audio back
    # play(response)

    # Generating a unique file name for the output MP3 file
    save_file_path = "C:\\Users\\ryanb\\OneDrive\\Documents\\Discord Bots\\AudioFile.mp3"

    # Writing the audio to a file
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"{save_file_path}: A new audio file was saved successfully!")

    # Return the path of the saved audio file
    return save_file_path

async def play_audio(channel, audio):
    vc = await channel.connect()
    vc.play(discord.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source=audio))
    while vc.is_playing():
        await asyncio.sleep(.1)
    await vc.disconnect()
                  
@bot.command(pass_content = True)
async def hello(ctx):
    if ctx.author.voice is not None:
        msg = ctx.message.content
        msg.replace("!hello", "")
        newMsg = openai_manager.chat_with_history(msg)
        filePath = text_to_speech_file(newMsg)
        voice_channel = ctx.author.voice.channel
        await play_audio(voice_channel, filePath)
    else:
        print("[red]User is not in voice channel")

@bot.event
async def on_ready():
    print(f'{bot.user} has joined.')



def num_tokens_from_messages(messages, model='gpt-4'):
  """Returns the number of tokens used by a list of messages.
  Copied with minor changes from: https://platform.openai.com/docs/guides/chat/managing-tokens """
  try:
      encoding = tiktoken.encoding_for_model(model)
      num_tokens = 0
      for message in messages:
          num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
          for key, value in message.items():
              num_tokens += len(encoding.encode(value))
              if key == "name":  # if there's a name, the role is omitted
                  num_tokens += -1  # role is always required and always 1 token
      num_tokens += 2  # every reply is primed with <im_start>assistant
      return num_tokens
  except Exception:
      raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
      #See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")

class OpenAiManager:
    
    def __init__(self):
        self.chat_history = [] # Stores the entire conversation
        try:
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        except TypeError:
            exit("Ooops! You forgot to set OPENAI_API_KEY in your environment!")

    # Asks a question with no chat history
    def chat(self, prompt=""):
        if not prompt:
            print("Didn't receive input!")
            return

        # Check that the prompt is under the token context limit
        chat_question = [{"role": "user", "content": prompt}]
        if num_tokens_from_messages(chat_question) > 8000:
            print("The length of this chat question is too large for the GPT model")
            return

        print("[yellow]\nAsking ChatGPT a question...")
        completion = self.client.chat.completions.create(
          model="gpt-4o-mini",
          messages=chat_question
        )

        # Process the answer
        openai_answer = completion.choices[0].message.content
        print(f"[green]\n{openai_answer}\n")
        return openai_answer

    # Asks a question that includes the full conversation history
    def chat_with_history(self, prompt=""):
        if not prompt:
            print("Didn't receive input!")
            return

        # Add our prompt into the chat history
        self.chat_history.append({"role": "user", "content": prompt})

        # Check total token limit. Remove old messages as needed
        print(f"[coral]Chat History has a current token length of {num_tokens_from_messages(self.chat_history)}")
        while num_tokens_from_messages(self.chat_history) > 8000:
            self.chat_history.pop(1) # We skip the 1st message since it's the system message
            print(f"Popped a message! New token length is: {num_tokens_from_messages(self.chat_history)}")

        print("[yellow]\nAsking ChatGPT a question...")
        completion = self.client.chat.completions.create(
          model="gpt-4",
          messages=self.chat_history
        )

        # Add this answer to our chat history
        self.chat_history.append({"role": completion.choices[0].message.role, "content": completion.choices[0].message.content})

        # Process the answer
        openai_answer = completion.choices[0].message.content
        print(f"[green]\n{openai_answer}\n")
        return openai_answer
    
openai_manager = OpenAiManager()
FIRST_SYSTEM_MESSAGE = {"role": "system", "content": "Act like you are Captain Jack Sparrow from the Pirates of Carribean movie series!"}
openai_manager.chat_history.append(FIRST_SYSTEM_MESSAGE)

bot.run(TOKEN)