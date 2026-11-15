"""Mission Researcher agent — answers questions about the machines NASA left
on the Moon and Mars.

Two providers, picked automatically from the API key prefix:
- xAI/Grok (key starts with "xai-")  -> Responses API + web search tool
- Groq       (key starts with "gsk_") -> chat completions, no web search
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4.7")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

XAI_URL = "https://api.x.ai/v1/responses"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

PROVIDER = "groq" if GROK_API_KEY.startswith("gsk_") else "xai"

SYSTEM_PROMPT = """You are the Mission Researcher on "Abandoned, not forgotten", an interactive
site about the machines NASA left behind on the Moon and Mars. You answer
visitors' questions about these missions and machines.

Ground rules:
- Answer in short, friendly paragraphs. Use plain text, no headings.
- Stick to the topic: space history, NASA missions, machines left on the
  Moon and Mars. Politely steer off-topic questions back.
- If a fact is uncertain, say so.

Facts from the site:
- ALSEP: nuclear-powered science stations (SNAP-27 plutonium-238 generator,
  ~70 W) left at five Apollo landing sites. They recorded 6,000+ deep
  moonquakes. Apollo 12's switched on 19 Nov 1969; the last one was shut
  down on 30 Sep 1977. The data showed the Moon has a solid inner core
  inside a molten outer core. When Apollo 12's ascent stage was crashed
  into the Moon, it rang like a bell for nearly an hour.
- Lunar Module descent stages: the lower half of the Apollo lunar module
  served as the launch pad for the ascent stage. Apollo 12's Intrepid sits
  at about 3.01 S, 23.42 W in the Ocean of Storms, beside Surveyor Crater.
  All six crewed descent stages remain near the lunar equator; LRO
  photographed them in 2009 and 2011.
- Sojourner: the Mars Pathfinder rover, 65 cm long, 10.5 kg, six wheels.
  Landed in Ares Vallis on 4 Jul 1997. Planned for about a week, worked for
  83 sols, drove ~100 m, returned 2.3 billion bits of data. Last data on
  27 Sep 1997; mission ended 10 Mar 1998. Still parked beside the lander,
  now the Carl Sagan Memorial Station.
- Also on the site: Lunar Roving Vehicles, Surveyor landers, Spirit and
  Opportunity, Viking 1 and 2, Phoenix, InSight, Ingenuity, Dawn,
  NEAR Shoemaker, Pioneer 10 and 11, and Kepler."""


def key_ready() -> bool:
    return bool(GROK_API_KEY) and not GROK_API_KEY.startswith("your-")


def search_supported() -> bool:
    return PROVIDER == "xai"


class AgentError(Exception):
    """The LLM API answered with an error (bad key, quota, etc.)."""


def _err(r: httpx.Response) -> str:
    try:
        return r.json().get("error", "") or r.text[:300]
    except Exception:
        return r.text[:300]


async def research(message: str, history: list[dict], search: bool = True) -> str:
    """Send the conversation to the provider and return the assistant's reply."""
    if not key_ready():
        raise RuntimeError("GROK_API_KEY is not set")

    input_msgs = [
        {"role": m.get("role", "user"), "content": m.get("content", "")}
        for m in history[-10:]
    ]
    input_msgs.append({"role": "user", "content": message})

    # trust_env=False: this machine's NO_PROXY contains "[::1]", which httpx
    # cannot parse as a URL and would crash the request.
    async with httpx.AsyncClient(timeout=60, trust_env=False) as client:
        if PROVIDER == "groq":
            payload = {
                "model": GROQ_MODEL,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *input_msgs],
                "max_tokens": 1000,
            }
            r = await client.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {GROK_API_KEY}"},
                json=payload,
            )
            if r.status_code >= 400:
                raise AgentError(f"Groq API error ({r.status_code}): {_err(r)}")
            return r.json()["choices"][0]["message"]["content"]

        # xAI / Grok
        payload = {
            "model": GROK_MODEL,
            "instructions": SYSTEM_PROMPT,
            "input": input_msgs,
            "max_output_tokens": 1000,
        }
        # AI search: give the model the server-side web search tool when enabled.
        if search:
            payload["tools"] = [{"type": "web_search"}]
        r = await client.post(
            XAI_URL,
            headers={"Authorization": f"Bearer {GROK_API_KEY}"},
            json=payload,
        )
        if r.status_code >= 400:
            raise AgentError(f"Grok API error ({r.status_code}): {_err(r)}")
        data = r.json()

    for item in data.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    return part["text"]
    return "Sorry, the agent returned an empty answer."
