import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, ValidationError

from src.config import (
    CONTROLLED_THEMES,
    GEMINI_API_KEY,
    LLM_API_KEY,
    LLM_CACHE_DIR,
    LLM_MAX_RPM,
    LLM_PROVIDER,
    MAX_LLM_CALLS,
    OFFLINE_MODE,
    OPENAI_API_KEY,
    get_logger,
)
from src.schemas import EventClass
from src.universe import CompanyExposure, load_universe, match_company

logger = get_logger("llm.client")


class RulesFallbackExtractor:
    """Deterministic, lexicon-driven fallback extractor when LLM is unavailable."""

    def __init__(self):
        self.universe: list[CompanyExposure] = load_universe()

    def extract(self, text: str) -> Dict[str, Any]:
        """Perform heuristic extraction on text returning schema-compliant dict."""
        lower = text.lower()

        # 1. Entity & Ticker
        matched = match_company(text, self.universe)
        if matched:
            entity = matched.name
            ticker = matched.ticker
            sector = matched.sector
            country = matched.country
        else:
            ticker = None
            if "red sea" in lower or "suez" in lower:
                entity = "Red Sea Shipping Disruption"
                sector = "Shipping"
                country = "EGY"
            elif "opec" in lower or "crude" in lower:
                entity = "OPEC Supply Cut"
                sector = "Energy"
                country = "SAU"
            elif "federal reserve" in lower or "repo" in lower:
                entity = "Federal Reserve Liquidity Facility"
                sector = "Banking"
                country = "USA"
            else:
                entity = text.split(":")[0][:40].strip() or "Market Participant"
                sector = "Financials"
                country = "USA"

        # 2. Event Class
        if any(w in lower for w in ["missile", "strike", "war", "naval", "red sea", "bab el-mandeb", "drone"]):
            event_class = EventClass.GEOPOLITICAL.value
        elif any(w in lower for w in ["opec", "inflation", "sofr", "crude", "barrel", "interest rate", "gdp", "production cut"]):
            event_class = EventClass.MACROECONOMIC.value
        elif any(w in lower for w in ["credit watch", "moratorium", "default", "downgrade", "debt facility", "liquidity check"]):
            event_class = EventClass.CREDIT_EVENT.value
        elif any(w in lower for w in ["antitrust", "probe", "investigation", "subpoena", "ftc", "sec", "regulatory", "faa"]):
            event_class = EventClass.REGULATORY.value
        elif any(w in lower for w in ["merger", "acquisition", "buyout", "takeover"]):
            event_class = EventClass.MERGER_ACQUISITION.value
        elif any(w in lower for w in ["launch", "unveil", "blackwell", "processor", "hardware update", "production volume"]):
            event_class = EventClass.PRODUCT_LAUNCH.value
        else:
            event_class = EventClass.OTHER.value

        # 3. Controlled Themes Mapping
        themes: List[str] = []
        if any(w in lower for w in ["missile", "shipping", "red sea", "suez", "bab el-mandeb", "transit indefinitely", "vessel"]):
            themes.append("shipping_disruption")
        if any(w in lower for w in ["opec", "crude cut", "production cut", "crude soaring", "oil soaring", "oil spikes", "brent spikes"]):
            themes.append("oil_price_up")
        elif any(w in lower for w in ["crude drop", "oil plunge", "crude tumble", "oil slides"]):
            themes.append("oil_price_down")
        if any(w in lower for w in ["downgrade", "credit watch", "negative outlook", "fitch", "moody"]):
            themes.append("credit_downgrade")
        if any(w in lower for w in ["moratorium", "default", "bankruptcy", "chapter 11", "distressed sovereign", "debt restructuring"]):
            themes.append("credit_default")
        if any(w in lower for w in ["banking stress", "bank run", "repo liquidity", "svb", "signature bank", "credit suisse", "deposit outflow", "liquidity check"]):
            themes.append("banking_stress")
        if any(w in lower for w in ["rate hike", "hikes 75bps", "tightens policy", "hawkish"]):
            themes.append("rate_hike")
        if any(w in lower for w in ["rate cut", "emergency cut", "dovish"]):
            themes.append("rate_cut")
        if any(w in lower for w in ["antitrust", "ftc probe", "doj probe", "subpoena", "monopoly"]):
            themes.append("antitrust")
        elif any(w in lower for w in ["regulatory action", "sec probe", "faa order", "compliance", "capital requirement"]):
            themes.append("regulatory_action")
        if any(w in lower for w in ["chip export", "semiconductor restriction", "tsmc fab", "foundry bottleneck", "blackwell delay"]):
            themes.append("chip_supply_shock")
        if any(w in lower for w in ["sanctions", "ofac", "trade ban", "embargo"]):
            themes.append("sanctions")
        if any(w in lower for w in ["lockdown", "travel ban", "grounding", "demand drop", "slump"]):
            themes.append("demand_shock")
        if any(w in lower for w in ["merger", "acquisition", "buyout", "takeover"]):
            themes.append("merger_activity")
        if not themes:
            themes = ["none"]
        themes = [t for t in themes if t in CONTROLLED_THEMES][:2]

        # 4. Claim Certainty
        if any(w in lower for w in ["rumor", "unverified", "whisper", "unconfirmed", "hearsay", "leak", "alleged", "discord"]):
            claim_certainty = "rumor"
        elif any(w in lower for w in ["reports", "sources", "reported", "channel checks"]):
            claim_certainty = "reported"
        else:
            claim_certainty = "confirmed"

        # 5. Impact Score (Anchored Rubric with improved shock lexicon)
        if any(w in lower for w in ["missile strike", "suspend all", "indefinitely", "moratorium", "opec+ emergency", "spikes 6.8%", "70% drop", "production cut sending crude oil soaring", "crude oil soaring 8%", "surprise 2m bpd"]):
            base_impact = 8.5
        elif any(w in lower for w in ["antitrust probe", "investigative demand", "negative credit watch", "reroutes", "surging", "45% overnight", "sanctions", "blockade", "downgrade", "default", "probe", "opec"]):
            base_impact = 7.5
        elif any(w in lower for w in ["investigation", "margin pressure", "inspection", "tightens underwriting", "export curb", "subpoena"]):
            base_impact = 5.5
        elif any(w in lower for w in ["three-year corporate", "credit facility", "debt facility", "resilient", "steady", "order backlogs", "commercial paper"]):
            base_impact = 3.2
        else:
            base_impact = 2.0

        # Rumors are down-weighted compared to confirmed stories
        if claim_certainty == "rumor":
            base_impact = max(1.5, base_impact - 2.5)

        impact_score = round(min(10.0, max(1.0, base_impact)), 1)

        # 6. Sentiment Score (perspective of entity market value)
        neg_words = ["strike", "suspend", "moratorium", "probe", "investigation", "pressure", "cautions", "glitch", "delay", "default", "drop", "spikes"]
        pos_words = ["record", "resilient", "expands", "surges", "growth", "priced", "calms", "advances", "successfully", "tight spread", "steady"]

        neg_count = sum(1 for w in neg_words if w in lower)
        pos_count = sum(1 for w in pos_words if w in lower)

        if "opec" in lower and ("exxon" in lower or "bp" in lower or "chevron" in lower or "energy" in lower):
            sentiment_score = 0.65  # OPEC cuts benefit oil producers
        elif "opec" in lower and "delta" in lower:
            sentiment_score = -0.70  # Oil spikes hurt airlines
        elif neg_count > pos_count:
            sentiment_score = round(max(-1.0, -0.4 - 0.15 * neg_count), 2)
        elif pos_count > neg_count:
            sentiment_score = round(min(1.0, 0.4 + 0.15 * pos_count), 2)
        else:
            sentiment_score = 0.0

        rationale = f"Evaluated via rule-based finance lexicon ({event_class}, {claim_certainty} status)."

        return {
            "entity": entity,
            "ticker": ticker,
            "sector": sector,
            "country": country,
            "themes": themes,
            "event_class": event_class,
            "sentiment_score": sentiment_score,
            "impact_score": impact_score,
            "claim_certainty": claim_certainty,
            "rationale": rationale[:160],
            "model_version": "rules-fallback",
        }


class LLMClient:
    """Unified client for LLM providers (Gemini, OpenAI, Anthropic) with cache, backoff, and fallback."""

    def __init__(
        self,
        provider: str = LLM_PROVIDER,
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        offline_mode: bool = OFFLINE_MODE,
        require_llm: bool = False,
    ):
        self.provider = (provider or "gemini").lower()
        self.api_key = api_key or LLM_API_KEY
        self.cache_dir = cache_dir or LLM_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.offline_mode = offline_mode
        self.require_llm = require_llm
        self.fallback = RulesFallbackExtractor()

        # Token & Call metrics
        self.call_count = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.estimated_cost_usd = 0.0
        self._quota_exhausted = False
        self._last_call_time = 0.0
        self._min_interval = 60.0 / max(1, LLM_MAX_RPM)

        # Provider model mapping
        if self.provider == "gemini":
            self.model_name = "gemini-3.6-flash"
            self.backup_model_name = "gemini-3.1-flash-lite"
        elif self.provider == "openai":
            self.model_name = "gpt-4o-mini"
            self.backup_model_name = "gpt-3.5-turbo"
        elif self.provider == "anthropic":
            self.model_name = "claude-3-5-haiku-latest"
            self.backup_model_name = "claude-3-haiku-20240307"
        else:
            self.model_name = "mock-model"
            self.backup_model_name = "mock-backup"

        self._init_provider_client()

    def _init_provider_client(self):
        """Initialize provider SDK client if credentials are present."""
        self._gemini_model = None
        self._gemini_backup_model = None
        self._openai_client = None

        if self.offline_mode or not self.api_key:
            logger.info("LLM Client operating in offline / fallback mode (no live calls).")
            return

        try:
            if self.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._gemini_model = genai.GenerativeModel(self.model_name)
                self._gemini_backup_model = genai.GenerativeModel(self.backup_model_name)
                logger.info("Initialized Gemini client with model: %s (backup: %s)", self.model_name, self.backup_model_name)
            elif self.provider == "openai":
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=self.api_key)
                logger.info("Initialized OpenAI client with model: %s", self.model_name)
        except Exception as e:
            logger.warning("Failed to initialize %s client (%s). Will use fallback.", self.provider, e)

    def _hash_request(self, system: str, user: str, temperature: float) -> str:
        """Create deterministic hash key for prompt and parameters."""
        raw = f"{self.provider}:{self.model_name}:{temperature}:{system}:{user}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _get_cached(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached LLM completion if present."""
        path = self.cache_dir / f"{key_hash}.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                return entry.get("response")
            except Exception as e:
                logger.warning("Error reading LLM cache %s: %s", path, e)
        return None

    def _set_cached(self, key_hash: str, response: Dict[str, Any], prompt_tokens: int = 0, comp_tokens: int = 0):
        """Write LLM response and usage to disk cache."""
        path = self.cache_dir / f"{key_hash}.json"
        entry = {
            "provider": self.provider,
            "model": self.model_name,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": comp_tokens,
            "response": response,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2)
        except Exception as e:
            logger.warning("Error writing LLM cache %s: %s", path, e)

    @staticmethod
    def _clean_json_str(text: str) -> str:
        """Strip markdown code block fences and isolate JSON body."""
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fence_match:
            return fence_match.group(1).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1].strip()
        return text.strip()

    def _throttle(self):
        """Throttle calls to provider free-tier RPM limits."""
        elapsed = time.time() - self._last_call_time
        if elapsed < self._min_interval:
            sleep_time = self._min_interval - elapsed
            logger.debug("Throttling LLM call for %.2fs to respect %d RPM limit", sleep_time, LLM_MAX_RPM)
            time.sleep(sleep_time)
        self._last_call_time = time.time()

    def _call_raw_provider(self, system: str, user: str, temperature: float) -> str:
        """Execute network call to the selected LLM provider with rate throttling."""
        self._throttle()

        if self.provider == "gemini" and self._gemini_model is not None:
            full_prompt = f"System Instructions:\n{system}\n\nUser Content:\n{user}"
            gen_config = {"temperature": temperature}
            try:
                resp = self._gemini_model.generate_content(full_prompt, generation_config=gen_config)
                return resp.text or ""
            except Exception as e:
                err_str = str(e).lower()
                if (
                    ("429" in err_str or "quota" in err_str or "resourceexhausted" in err_str)
                    and self._gemini_backup_model is not None
                    and self.model_name != self.backup_model_name
                ):
                    logger.warning(
                        "Primary Gemini model %s quota exceeded. Failing over to backup: %s",
                        self.model_name,
                        self.backup_model_name,
                    )
                    self._gemini_model = self._gemini_backup_model
                    self.model_name = self.backup_model_name
                    resp = self._gemini_model.generate_content(full_prompt, generation_config=gen_config)
                    return resp.text or ""
                raise

        if self.provider == "openai" and self._openai_client is not None:
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
            resp = self._openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            return resp.choices[0].message.content or ""

        raise RuntimeError(f"No configured LLM provider client available for {self.provider}")

    def complete_json(
        self,
        system: str,
        user: str,
        schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.0,
        require_llm: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Complete prompt and return validated JSON dict with caching, retry, and fallback."""
        must_require_llm = self.require_llm if require_llm is None else require_llm
        key_hash = self._hash_request(system, user, temperature)

        # 1. Check cache first
        cached = self._get_cached(key_hash)
        if cached is not None:
            logger.debug("LLM cache HIT for prompt hash %s", key_hash[:8])
            return cached

        # 2. Check offline mode or missing credentials or quota exhausted
        if self.offline_mode or not self.api_key or self._quota_exhausted:
            if must_require_llm:
                raise RuntimeError("LLM execution required (--require-llm) but client is offline/no-key/quota exhausted.")
            logger.debug("Operating in offline/fallback mode. Using rules-fallback extractor.")
            return self.fallback.extract(user)

        # 3. Check call quota limit
        if self.call_count >= MAX_LLM_CALLS:
            if must_require_llm:
                raise RuntimeError(f"MAX_LLM_CALLS limit ({MAX_LLM_CALLS}) reached with --require-llm active.")
            logger.warning("MAX_LLM_CALLS limit (%d) reached. Falling back to rules.", MAX_LLM_CALLS)
            return self.fallback.extract(user)

        # 4. Live execution with retry & backoff
        current_user_prompt = user
        last_error = ""

        for attempt in range(4):
            try:
                self.call_count += 1
                raw_text = self._call_raw_provider(system, current_user_prompt, temperature)

                # Estimate tokens
                p_tokens = len(current_user_prompt.split()) * 2
                c_tokens = len(raw_text.split()) * 2
                self.total_prompt_tokens += p_tokens
                self.total_completion_tokens += c_tokens
                self.estimated_cost_usd += (p_tokens * 0.00000015) + (c_tokens * 0.0000006)

                cleaned = self._clean_json_str(raw_text)
                parsed_dict = json.loads(cleaned)

                # Validate with schema if provided
                if schema is not None:
                    validated = schema.model_validate(parsed_dict)
                    result_dict = validated.model_dump()
                else:
                    result_dict = parsed_dict

                result_dict["model_version"] = f"{self.provider}-{self.model_name}"
                self._set_cached(key_hash, result_dict, prompt_tokens=p_tokens, comp_tokens=c_tokens)
                return result_dict

            except (json.JSONDecodeError, ValidationError) as e:
                last_error = str(e)
                logger.warning("LLM attempt %d failed validation: %s. Retrying...", attempt + 1, last_error[:100])
                current_user_prompt = (
                    f"{user}\n\nPREVIOUS ATTEMPT RETURNED INVALID JSON/SCHEMA:\n{last_error}\n"
                    f"Please output strictly valid raw JSON adhering to the specified fields."
                )
            except Exception as ex:
                err_msg = str(ex).lower()
                last_error = str(ex)
                if "429" in err_msg or "quota" in err_msg or "resourceexhausted" in err_msg:
                    # Exponential backoff with retry-after hint parsing
                    hint_match = re.search(r"seconds:\s*(\d+)", err_msg) or re.search(r"retry in (\d+)", err_msg)
                    if hint_match:
                        raw_delay = float(hint_match.group(1))
                        if raw_delay > 60.0:
                            logger.warning(
                                "Daily quota limit exceeded (hint %.0fs > 60s). Marking quota exhausted.",
                                raw_delay,
                            )
                            self._quota_exhausted = True
                            if must_require_llm:
                                raise RuntimeError(f"Daily quota limit exceeded with --require-llm: {last_error}")
                            break
                        backoff_delay = raw_delay + 2.0
                    else:
                        backoff_delay = min(45.0, 10.0 * (2 ** attempt))

                    logger.warning(
                        "LLM HTTP 429/quota encountered. Backing off for %.1fs (attempt %d/4)...",
                        backoff_delay,
                        attempt + 1,
                    )
                    time.sleep(backoff_delay)
                else:
                    logger.warning("LLM network/API error on attempt %d: %s", attempt + 1, ex)
                    time.sleep(3.0)

        # Fallback if retries exhausted
        if must_require_llm:
            raise RuntimeError(f"All LLM attempts exhausted with --require-llm: {last_error}")

        logger.warning("All LLM attempts exhausted. Using rules-fallback extractor.")
        return self.fallback.extract(user)
