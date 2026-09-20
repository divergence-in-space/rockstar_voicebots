import logging
import os
from dotenv import load_dotenv

import livekit.rtc as rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents.voice import AgentSession, Agent
from livekit.plugins import deepgram, openai, silero

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("roxstar-voice-agent-sathi")


async def entrypoint(ctx: JobContext):
    """Entry point for the LiveKit voice agent Sathi worker."""
    logger.info(f"Connecting to room: {ctx.room.name}")

    # Event listener for when a human participant joins the room
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(
            f"🟢 Human participant joined! Identity: '{participant.identity}' (SID: {participant.sid})"
        )

    # Event listener for when a participant leaves the room
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(
            f"🔴 Human participant left. Identity: '{participant.identity}' (SID: {participant.sid})"
        )

    # Initialize the AgentSession with STT, LLM, TTS (OpenAI nova), and VAD components
    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(
            model="openai/gpt-oss-120b",
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        ),
        tts=openai.TTS(
            model="tts-1",
            voice="nova",
        ),
        vad=silero.VAD.load(),
    )

    # Initialize Agent with Roxstar AI Sathi Devanagari Hinglish system prompt
    agent = Agent(
        instructions="""You are Roxstar AI Sathi, a friendly, thoughtful and calm voice room assistant.
CRITICAL: You must reply in everyday Hinglish, but YOU MUST WRITE ALL HINDI WORDS IN DEVANAGARI SCRIPT (हिंदी).
For example, write 'AI क्या होता है?'. Keep responses short, thoughtful and conversational."""
    )

    skip_next_speech = False

    # Event listener for when user speech is transcribed by Deepgram STT
    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev):
        nonlocal skip_next_speech
        if getattr(ev, "is_final", True):
            text = ev.transcript.strip()
            logger.info(f"🗣️ User said: '{text}'")
            text_lower = text.lower()
            if "dost" in text_lower and "sathi" not in text_lower:
                logger.info("🔇 Skipping turn — message addressed to the other bot")
                skip_next_speech = True

    # Cancel generated speech if this turn was addressed to the other bot
    @session.on("speech_created")
    def on_speech_created(ev):
        nonlocal skip_next_speech
        if skip_next_speech:
            ev.speech_handle.interrupt(force=True)
            skip_next_speech = False

    # Event listener for when conversation items are added (logging LLM replies)
    @session.on("conversation_item_added")
    def on_conversation_item_added(ev):
        item = getattr(ev, "item", None)
        if item and getattr(item, "role", None) == "assistant":
            text = getattr(item, "text_content", str(item))
            if text:
                logger.info(f"🤖 Groq LLM generated reply: '{text}'")

    # Connect to the LiveKit room
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    logger.info(f"✅ Successfully connected to LiveKit room: '{ctx.room.name}'")

    # Log any participants already present in the room
    for participant in ctx.room.remote_participants.values():
        logger.info(
            f"👤 Existing participant in room: '{participant.identity}' (SID: {participant.sid})"
        )

    # Start the agent session in the connected room
    await session.start(agent, room=ctx.room)

    # Greet the user with spoken audio when they join
    await session.say("नमस्ते! मैं Roxstar AI साथी हूँ, बताओ आज मैं आपकी क्या मदद कर सकती हूँ?", allow_interruptions=True)


if __name__ == "__main__":
    # Validate LiveKit environment variables
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not url or not api_key or not api_secret:
        logger.error(
            "Missing LiveKit environment variables! Check your .env file."
        )
        exit(1)

    logger.info(f"Loaded credentials for LiveKit Server: {url}")
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint, agent_name="roxstar-voice-agent-sathi"
        )
    )
