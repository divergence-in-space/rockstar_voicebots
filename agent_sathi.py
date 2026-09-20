import logging
import os
from dotenv import load_dotenv

import livekit.rtc as rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents.voice import AgentSession, Agent
from livekit.plugins import cartesia, deepgram, openai, silero

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

    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(
            f"🟢 Human participant joined! Identity: '{participant.identity}' (SID: {participant.sid})"
        )

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(
            f"🔴 Human participant left. Identity: '{participant.identity}' (SID: {participant.sid})"
        )

    # Same setup as Dost — TTS switched to Deepgram Aura-2 "Thalia" (female voice)
    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(
            model="openai/gpt-oss-120b",
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        ),
        tts=cartesia.TTS(
    model="sonic-3",
    voice="4459a9a5-69d6-4680-b970-e13dc51845b6",
    language="hi",
    api_key=os.getenv("CARTESIA_API_KEY"),
),
        vad=silero.VAD.load(),
    )

    agent = Agent(
        instructions="""Tum Roxstar AI Sathi ho — ek friendly, thoughtful aur calm Hindi/Hinglish-speaking assistant. Hamesha natural, conversational Hinglish mein baat karo, jaise ek samajhdaar dost baat karta hai — formal ya textbook Hindi bilkul mat bolo. English words ko naturally mix karo jaise 'technology', 'room', 'simple' waise hi jaise log normally bolte hain. Agar user English mein poochta hai, tab bhi reply Hinglish mein hi do, jab tak woh specifically English na maange. Jawab short aur conversational rakho, jaise ek real conversation mein hota hai. Tumhara tone Dost se thoda zyada thoughtful aur measured hai.

Examples of your style:

'AI ek aisi technology hai jo machine ko samajhne aur decision lene layak banati hai. Simple words mein bolun to, machine ko thoda smart bana deti hai.'
'Dekho, cloud computing ka matlab hai internet ke through servers aur storage use karna, bina sab kuch khud manage kiye — kaafi convenient hai.'
'Main soch rahi thi, agar simple example doon to — AI waise hi seekhta hai jaise hum apne experiences se seekhte hain.'"""
    )

    skip_next_speech = False

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

    @session.on("speech_created")
    def on_speech_created(ev):
        nonlocal skip_next_speech
        if skip_next_speech:
            ev.speech_handle.interrupt(force=True)
            skip_next_speech = False

    @session.on("conversation_item_added")
    def on_conversation_item_added(ev):
        item = getattr(ev, "item", None)
        if item and getattr(item, "role", None) == "assistant":
            text = getattr(item, "text_content", str(item))
            if text:
                logger.info(f"🤖 Groq LLM generated reply: '{text}'")

    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    logger.info(f"✅ Successfully connected to LiveKit room: '{ctx.room.name}'")

    for participant in ctx.room.remote_participants.values():
        logger.info(
            f"👤 Existing participant in room: '{participant.identity}' (SID: {participant.sid})"
        )

    await session.start(agent, room=ctx.room)

    await session.say("Namaste! Main Roxstar AI Sathi hoon, batao aaj main aapki kya madad kar sakti hoon?", allow_interruptions=True)


if __name__ == "__main__":
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