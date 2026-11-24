import os
import json
import math
import hmac
import random
import hashlib
import secrets
import datetime
import requests
from pathlib import Path
import pandas as pd
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from guides_data import (
    ExamType,
    ThematicAxis,
    DEMREExhaustiveGuide,
    get_exhaustive_guides_by_exam,
)
from demre_ingestion_pipeline import (
    GoPAESVectorStore,
    AXIS_LABELS,
    OFFICIAL_PAES_65_DISTRIBUTION,
    DEMREQuestionNode,
)
from adaptive_engine import (
    GoPAESAdaptiveEngine,
    GoPAESProfileManager,
    GoPAESLLMCoach,
    AxisMasteryState,
    SelectionMode,
    OFFICIAL_SECONDS_PER_QUESTION,
    ALL_AXES,
)

# Compatibilidad automática con claves AQ.Ab8RN... y modelos Gemini 3.x / 2.5
GoPAESLLMCoach.GEMINI_MODELS_CASCADE = [
    "gemini-3.1-flash-lite-preview",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash-latest",
]


@classmethod
def _validate_key_accepting_aq(cls, provider: str, api_key: str | None) -> tuple[bool, str]:
    if not api_key:
        return False, "Sin clave configurada"
    if provider == "gemini" and not api_key.startswith(("AIza", "AQ.")):
        return False, "Formato no reconocido"
    if provider == "openai" and not api_key.startswith("sk-"):
        return False, "Formato no reconocido"
    return True, "En línea"


GoPAESLLMCoach.validate_key_format = _validate_key_accepting_aq

# =====================================================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT - GOPAES
# =====================================================================
st.set_page_config(
    page_title="GoPAES | Preuniversitario Gamificado PAES (M1 y M2)",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# ESTILOS CSS PERSONALIZADOS (ESTÉTICA GAMIFICADA LIMPIA GOPAES)
# =====================================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background-color: #FAF9F5;
        color: #0F172A;
    }

    /* Tarjetas blancas redondeadas con sombra suave */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 20px !important;
        padding: 1.35rem !important;
        box-shadow: 0 4px 16px -4px rgba(15, 23, 42, 0.04) !important;
    }

    /* Botones principales estilo cápsula verde oscuro e índigo */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #065F46 0%, #047857 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 0.55rem 1.3rem !important;
        font-weight: 700 !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(4, 120, 87, 0.25) !important;
    }

    div.stButton > button[kind="secondary"] {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 999px !important;
        padding: 0.5rem 1.2rem !important;
        font-weight: 600 !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #F1F5F9 !important;
        border-color: #94A3B8 !important;
    }

    /* Barra superior GoPAES */
    .gopaes-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 18px;
        padding: 12px 24px;
        margin-bottom: 18px;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
        flex-wrap: wrap;
        gap: 12px;
    }
    .gopaes-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .gopaes-logo-text {
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #0F172A;
    }
    .gopaes-badge-pill {
        background-color: #DCFCE7;
        color: #15803D;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 999px;
        border: 1px solid #BBF7D0;
    }
    .gopaes-user-pills {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .gopaes-stat-pill {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 999px;
        padding: 5px 12px;
        font-size: 0.85rem;
        font-weight: 700;
        color: #1E293B;
    }
    .gopaes-avatar-pill {
        display: flex;
        align-items: center;
        gap: 8px;
        background: #EEF2FF;
        border: 1px solid #C7D2FE;
        border-radius: 999px;
        padding: 4px 14px 4px 6px;
        font-size: 0.88rem;
        font-weight: 700;
        color: #1E1B4B;
    }
    .gopaes-avatar-circle {
        background: #2563EB;
        color: #FFFFFF;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 800;
    }

    /* Hero Banner Azul/Índigo Gamificado */
    .gopaes-hero {
        background: linear-gradient(135deg, #2536EB 0%, #3729CC 52%, #2E1065 100%);
        border-radius: 26px;
        padding: 34px 36px;
        color: #FFFFFF;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 24px;
        margin-bottom: 22px;
        box-shadow: 0 14px 30px -10px rgba(37, 54, 235, 0.35);
    }
    .gopaes-hero-tag {
        display: inline-block;
        background: rgba(255, 255, 255, 0.16);
        backdrop-filter: blur(8px);
        color: #E0E7FF;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 999px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .gopaes-hero-title {
        font-size: 2.35rem;
        font-weight: 800;
        margin: 0 0 8px 0;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }
    .gopaes-hero-sub {
        font-size: 1rem;
        color: #DBEAFE;
        margin: 0;
        max-width: 540px;
        line-height: 1.5;
    }
    .gopaes-hero-stats {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
    }
    .gopaes-glass-box {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.22);
        border-radius: 18px;
        padding: 14px 18px;
        min-width: 92px;
        text-align: center;
    }
    .gopaes-glass-label {
        font-size: 0.76rem;
        color: #C7D2FE;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .gopaes-glass-val {
        font-size: 1.45rem;
        font-weight: 800;
        color: #FFFFFF;
    }

    /* Banner Diagnóstico celeste suave */
    .gopaes-diag-strip {
        background: linear-gradient(90deg, #EFF6FF 0%, #F8FAFC 100%);
        border: 1px solid #BFDBFE;
        border-radius: 20px;
        padding: 18px 24px;
        margin-bottom: 8px;
    }

    /* Cabeceras de tarjetas de modos principales */
    .mode-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }
    .mode-icon-box {
        width: 46px;
        height: 46px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.35rem;
    }
    .mode-pill {
        font-size: 0.76rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 999px;
    }
    .elo-inner-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 12px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 14px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# INICIALIZACIÓN DE BASE VECTORIAL QDRANT
# =====================================================================
if "vector_store" not in st.session_state:
    store = GoPAESVectorStore()
    seeded_nodes = store.seed_official_demre_questions()
    st.session_state.vector_store = store
    st.session_state.total_indexed_nodes = len(seeded_nodes)

if "active_username" not in st.session_state:
    st.session_state.active_username = None

if "nav_section" not in st.session_state:
    # 'DASHBOARD' | 'DIAGNOSTIC' | 'EXAMS' | 'GUIDES_M1' | 'GUIDES_M2' | 'DUEL_1V1' | 'RANKING'
    st.session_state.nav_section = "DASHBOARD"

if "exam_subphase" not in st.session_state:
    st.session_state.exam_subphase = "CONFIG"

if "diag_questions" not in st.session_state:
    all_nodes = st.session_state.vector_store.get_all_nodes(exam="M1")
    anchors = [q for q in all_nodes if q.is_diagnostic_anchor][:4]
    st.session_state.diag_questions = anchors
    st.session_state.diag_idx = 0

if "asked_ids" not in st.session_state:
    st.session_state.asked_ids = []

if "exam_queue" not in st.session_state:
    st.session_state.exam_queue = []

if "exam_history" not in st.session_state:
    st.session_state.exam_history = []

if "ai_explanations_cache" not in st.session_state:
    st.session_state.ai_explanations_cache = {}

if "interleaved_feedback" not in st.session_state:
    st.session_state.interleaved_feedback = {}

if "selected_guide_axis" not in st.session_state:
    st.session_state.selected_guide_axis = None

if "unit_custom_workouts" not in st.session_state:
    st.session_state.unit_custom_workouts = {}

if "unit_workout_answers" not in st.session_state:
    st.session_state.unit_workout_answers = {}

if "exam_config" not in st.session_state:
    st.session_state.exam_config = {
        "exam": "M1",
        "num_questions": 5,
        "timed_mode": True,
        "selection_mode": "ADAPTIVE",
        "focus_axis": None,
    }

# Estado del modo multijugador Duelo 1v1
if "duel_state" not in st.session_state:
    st.session_state.duel_state = {
        "phase": "LOBBY",  # 'LOBBY' | 'ACTIVE_DUEL' | 'DUEL_RESULTS'
        "room_code": None,
        "exam": "M1",
        "opponent_name": "Rival",
        "opponent_elo": 1000,
        "opponent_answers": [],  # lista de bool (acierto/fallo del rival por pregunta)
        "questions": [],
        "player_history": [],
        "elo_delta": 0,
        "is_room_creator": False,
    }

UNIT_ICONS: dict[ThematicAxis, str] = {
    "NUMEROS": "🔢",
    "ALGEBRA_Y_FUNCIONES": "📈",
    "GEOMETRIA": "📐",
    "PROBABILIDAD_Y_ESTADISTICA": "📊",
}

UNIT_NUMBER_LABELS: dict[ThematicAxis, str] = {
    "NUMEROS": "Unidad 1: Números",
    "ALGEBRA_Y_FUNCIONES": "Unidad 2: Álgebra y Funciones",
    "GEOMETRIA": "Unidad 3: Geometría",
    "PROBABILIDAD_Y_ESTADISTICA": "Unidad 4: Probabilidad y Estadística",
}


# =====================================================================
# GESTOR MULTIJUGADOR 1V1, SISTEMA ELO Y LIGAS (LOCAL + SUPABASE)
# =====================================================================
DUELS_STORAGE_PATH = Path("./storage/gopaes_duels.json")


def get_league_info(elo: int) -> tuple[str, str, str]:
    """
    Retorna (nombre_liga, color_fondo_hex, color_texto_hex) según el puntaje ELO.
    """
    if elo >= 1400:
        return "💎 Liga Diamante", "#DBEAFE", "#1D4ED8"
    if elo >= 1220:
        return "🥇 Liga Oro", "#FEF3C7", "#B45309"
    if elo >= 1080:
        return "🥈 Liga Plata", "#F1F5F9", "#334155"
    return "🥉 Liga Bronce", "#FFEDD5", "#C2410C"


def get_profile_elo(prof) -> int:
    val = getattr(prof, "elo_rating", None)
    if val is not None:
        return int(val)
    mu = getattr(prof, "micro_units_state", {}) or {}
    if "__GAMIFICATION__" in mu:
        g = mu["__GAMIFICATION__"]
        c = getattr(g, "correct_count", 1000) if not isinstance(g, dict) else g.get("correct_count", 1000)
        return int(c or 1000)
    return 1000


def get_profile_wins(prof) -> int:
    val = getattr(prof, "duel_wins", None)
    if val is not None:
        return int(val)
    mu = getattr(prof, "micro_units_state", {}) or {}
    if "__GAMIFICATION__" in mu:
        g = mu["__GAMIFICATION__"]
        w = getattr(g, "incorrect_count", 0) if not isinstance(g, dict) else g.get("incorrect_count", 0)
        return int(w or 0)
    return 0


def set_profile_elo_and_wins(prof, new_elo: int, new_wins: int, new_losses: int = 0):
    try:
        prof.elo_rating = new_elo
        prof.duel_wins = new_wins
        prof.duel_losses = new_losses
    except Exception:
        pass
    GoPAESProfileManager.save_profile(prof)


def calculate_elo_change(player_elo: int, opponent_elo: int, outcome: float) -> int:
    """
    Fórmula oficial ELO (K=32). outcome = 1.0 (victoria), 0.5 (empate), 0.0 (derrota).
    """
    expected = 1.0 / (1.0 + math.pow(10.0, (opponent_elo - player_elo) / 400.0))
    return int(round(32.0 * (outcome - expected)))


def load_shared_duel_rooms() -> list[dict]:
    DUELS_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    local_rooms: list[dict] = []
    if DUELS_STORAGE_PATH.exists():
        try:
            local_rooms = json.loads(DUELS_STORAGE_PATH.read_text(encoding="utf-8"))
        except Exception:
            local_rooms = []

    # Intentar sincronizar salas multijugador desde Supabase (fila especial __GOPAES_MULTIPLAYER_LOBBY__)
    if hasattr(GoPAESProfileManager, "resolve_supabase_credentials"):
        url, key, _ = GoPAESProfileManager.resolve_supabase_credentials()
        if url and key:
            endpoint = f"{url}/rest/v1/gopaes_profiles?username=eq.__GOPAES_MULTIPLAYER_LOBBY__&select=axes_state"
            try:
                resp = requests.get(
                    endpoint,
                    headers={"apikey": key, "Authorization": f"Bearer {key}"},
                    timeout=8,
                )
                if resp.status_code == 200:
                    rows = resp.json()
                    if rows and isinstance(rows[0].get("axes_state"), dict):
                        cloud_rooms = rows[0]["axes_state"].get("rooms", [])
                        if isinstance(cloud_rooms, list):
                            by_code = {r["room_code"]: r for r in local_rooms if "room_code" in r}
                            for cr in cloud_rooms:
                                if "room_code" in cr:
                                    by_code[cr["room_code"]] = cr
                            return list(by_code.values())
            except Exception:
                pass
    return local_rooms


def save_shared_duel_rooms(rooms: list[dict]) -> None:
    DUELS_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    trimmed = rooms[-40:]
    DUELS_STORAGE_PATH.write_text(json.dumps(trimmed, ensure_ascii=False, indent=2), encoding="utf-8")

    if hasattr(GoPAESProfileManager, "resolve_supabase_credentials"):
        url, key, _ = GoPAESProfileManager.resolve_supabase_credentials()
        if url and key:
            endpoint = f"{url}/rest/v1/gopaes_profiles"
            payload = {
                "username": "__GOPAES_MULTIPLAYER_LOBBY__",
                "password_hash": "SYSTEM",
                "password_salt": "SYSTEM",
                "created_at": datetime.date.today().isoformat(),
                "last_activity_date": datetime.date.today().isoformat(),
                "study_streak": 0,
                "completed_exams": 0,
                "diagnostic_completed": False,
                "axes_state": {"rooms": trimmed},
                "micro_units_state": {},
                "logs": [],
            }
            try:
                requests.post(
                    endpoint,
                    json=payload,
                    headers={
                        "apikey": key,
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                        "Prefer": "resolution=merge-duplicates",
                    },
                    timeout=8,
                )
            except Exception:
                pass


def get_global_leaderboard() -> list[dict]:
    """
    Construye el Ranking Global unificando los usuarios reales de Supabase + almacenamiento local
    y bots de referencia de las ligas si aún hay pocos jugadores registrados.
    """
    entries: dict[str, dict] = {}

    if hasattr(GoPAESProfileManager, "fetch_all_profiles_for_leaderboard"):
        all_profs = GoPAESProfileManager.fetch_all_profiles_for_leaderboard()
        for p in all_profs:
            if p.username.startswith("__GOPAES_"):
                continue
            tot_c = sum(s.correct_count for s in p.axes_state.values())
            tot_i = sum(s.incorrect_count for s in p.axes_state.values())
            acc = round((tot_c / (tot_c + tot_i)) * 100, 1) if (tot_c + tot_i) > 0 else 0.0
            entries[p.username] = {
                "username": p.username,
                "elo": get_profile_elo(p),
                "wins": get_profile_wins(p),
                "streak": p.study_streak,
                "accuracy": acc,
                "is_real": True,
            }
    else:
        for uname in GoPAESProfileManager.list_existing_profiles():
            if uname.startswith("__GOPAES_"):
                continue
            p = GoPAESProfileManager.load_or_create_profile(uname)
            tot_c = sum(s.correct_count for s in p.axes_state.values())
            tot_i = sum(s.incorrect_count for s in p.axes_state.values())
            acc = round((tot_c / (tot_c + tot_i)) * 100, 1) if (tot_c + tot_i) > 0 else 0.0
            entries[p.username] = {
                "username": p.username,
                "elo": get_profile_elo(p),
                "wins": get_profile_wins(p),
                "streak": p.study_streak,
                "accuracy": acc,
                "is_real": True,
            }

    # Añadir postulantes de referencia de las ligas GoPAES para que el ranking y matchmaking siempre estén vivos
    reference_postulantes = [
        {"username": "Valentina_M2", "elo": 1420, "wins": 18, "streak": 12, "accuracy": 91.5, "is_real": False},
        {"username": "Matias_DEMRE", "elo": 1295, "wins": 11, "streak": 7, "accuracy": 84.0, "is_real": False},
        {"username": "Camila_UC", "elo": 1170, "wins": 6, "streak": 5, "accuracy": 78.2, "is_real": False},
        {"username": "Lucas_Beauchef", "elo": 1060, "wins": 3, "streak": 3, "accuracy": 71.0, "is_real": False},
        {"username": "Sofia_PAES", "elo": 1015, "wins": 1, "streak": 2, "accuracy": 65.4, "is_real": False},
    ]
    for ref in reference_postulantes:
        if ref["username"] not in entries:
            entries[ref["username"]] = ref

    ranked = list(entries.values())
    ranked.sort(key=lambda x: (x["elo"], x["wins"], x["accuracy"]), reverse=True)
    for idx, item in enumerate(ranked, start=1):
        item["rank"] = idx
    return ranked


# =====================================================================
# SISTEMA DE AUTENTICACIÓN SEGURO (USUARIO + CONTRASEÑA)
# =====================================================================
AUTH_CREDENTIALS_PATH = Path("./storage/gopaes_credentials.json")


def _hash_pwd_local(password: str, salt_hex: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        100_000,
    )
    return dk.hex()


def _load_credentials_store() -> dict:
    AUTH_CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not AUTH_CREDENTIALS_PATH.exists():
        AUTH_CREDENTIALS_PATH.write_text("{}", encoding="utf-8")
        return {}
    try:
        return json.loads(AUTH_CREDENTIALS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_credentials_store(data: dict) -> None:
    AUTH_CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUTH_CREDENTIALS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def register_student_account(username: str, password: str, confirm_password: str) -> tuple[bool, str]:
    clean_user = username.strip()
    if not clean_user:
        return False, "Por favor escribe un nombre de usuario."
    if len(clean_user) < 3:
        return False, "El nombre de usuario debe tener al menos 3 caracteres."
    if len(password) < 4:
        return False, "La contraseña debe tener al menos 4 caracteres."
    if password != confirm_password:
        return False, "Las contraseñas no coinciden. Verifícalas e inténtalo de nuevo."

    if hasattr(GoPAESProfileManager, "register_user"):
        ok, msg, prof = GoPAESProfileManager.register_user(clean_user, password)
        if not ok or prof is None:
            return False, msg
        st.session_state.active_username = prof.username
        st.session_state.engine = GoPAESAdaptiveEngine(profile=prof)
        st.session_state.nav_section = "DASHBOARD"
        return True, msg

    creds = _load_credentials_store()
    existing_key = next((k for k in creds.keys() if k.lower() == clean_user.lower()), None)
    if existing_key is not None:
        return False, f"El usuario '{existing_key}' ya está registrado. Ve a la pestaña 'Iniciar Sesión'."

    salt_hex = secrets.token_hex(16)
    pwd_hash = _hash_pwd_local(password, salt_hex)
    creds[clean_user] = {"salt": salt_hex, "hash": pwd_hash}
    _save_credentials_store(creds)

    prof = GoPAESProfileManager.load_or_create_profile(clean_user)
    st.session_state.active_username = prof.username
    st.session_state.engine = GoPAESAdaptiveEngine(profile=prof)
    st.session_state.nav_section = "DASHBOARD"
    return True, f"Cuenta creada exitosamente para {prof.username}."


def authenticate_student_account(username: str, password: str) -> tuple[bool, str]:
    clean_user = username.strip()
    if not clean_user or not password:
        return False, "Por favor ingresa tu nombre de usuario y tu contraseña."

    if hasattr(GoPAESProfileManager, "authenticate_user"):
        ok, msg, prof = GoPAESProfileManager.authenticate_user(clean_user, password)
        if not ok or prof is None:
            return False, msg
        st.session_state.active_username = prof.username
        st.session_state.engine = GoPAESAdaptiveEngine(profile=prof)
        st.session_state.nav_section = "DASHBOARD"
        return True, msg

    creds = _load_credentials_store()
    matched_key = next((k for k in creds.keys() if k.lower() == clean_user.lower()), None)
    existing_profiles = GoPAESProfileManager.list_existing_profiles()
    matched_prof_name = next((p for p in existing_profiles if p.lower() == clean_user.lower()), None)

    if matched_key is None:
        if matched_prof_name is not None:
            salt_hex = secrets.token_hex(16)
            creds[matched_prof_name] = {
                "salt": salt_hex,
                "hash": _hash_pwd_local(password, salt_hex),
            }
            _save_credentials_store(creds)
            prof = GoPAESProfileManager.load_or_create_profile(matched_prof_name)
            st.session_state.active_username = prof.username
            st.session_state.engine = GoPAESAdaptiveEngine(profile=prof)
            st.session_state.nav_section = "DASHBOARD"
            return True, f"Contraseña vinculada e inicio de sesión exitoso para {prof.username}."
        return False, f"No existe una cuenta con el usuario '{clean_user}'. Regístrate en la pestaña 'Registrarse'."

    entry = creds[matched_key]
    cand_hash = _hash_pwd_local(password, entry["salt"])
    if not hmac.compare_digest(entry["hash"], cand_hash):
        return False, "❌ Contraseña incorrecta. Inténtalo de nuevo."

    prof = GoPAESProfileManager.load_or_create_profile(matched_key)
    st.session_state.active_username = prof.username
    st.session_state.engine = GoPAESAdaptiveEngine(profile=prof)
    st.session_state.nav_section = "DASHBOARD"
    return True, f"Bienvenido nuevamente, {prof.username}."


def logout_profile():
    st.session_state.active_username = None
    st.session_state.selected_guide_axis = None
    st.rerun()


# =====================================================================
# PANTALLA DE INICIO DE SESIÓN Y REGISTRO CON ESTÉTICA GAMIFICADA
# =====================================================================
if not st.session_state.active_username:
    st.markdown(
        """
        <div class="gopaes-hero" style="margin-top: 10px;">
            <div>
                <div class="gopaes-hero-tag">✨ Preuniversitario Gamificado GoPAES</div>
                <h1 class="gopaes-hero-title">Domina la PAES M1 y M2</h1>
                <p class="gopaes-hero-sub">
                    Entrena con ensayos adaptativos oficiales del DEMRE, guías paso a paso con validación inmediata,
                    duelos 1v1 en vivo con rating ELO y Coaching IA en LaTeX.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs([
        "🔐 Iniciar Sesión (Ya tengo cuenta)",
        "📝 Registrarse (Crear cuenta nueva)",
    ])

    with tab_login:
        with st.container(border=True):
            st.subheader("🔐 Iniciar Sesión en GoPAES")
            st.caption("Ingresa tu usuario y contraseña para continuar tu racha y defender tu Rating ELO:")
            login_user = st.text_input(
                "Nombre de Usuario:",
                placeholder="Ej: Antonio",
                key="login_username_input",
            )
            login_pwd = st.text_input(
                "Contraseña:",
                type="password",
                placeholder="Ingresa tu contraseña",
                key="login_password_input",
            )

            if st.button("🔓 Entrar a GoPAES →", type="primary", use_container_width=True, key="btn_do_login"):
                ok, msg = authenticate_student_account(login_user, login_pwd)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with tab_register:
        with st.container(border=True):
            st.subheader("📝 Crear Nueva Cuenta de Estudiante")
            st.caption(
                "Registra tu usuario y contraseña personal para guardar tu progreso en la nube y clasificar en las Ligas 1v1."
            )
            reg_user = st.text_input(
                "Elige un Nombre de Usuario:",
                placeholder="Ej: Antonio",
                key="reg_username_input",
            )
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                reg_pwd = st.text_input(
                    "Crea tu Contraseña (mín. 4 caracteres):",
                    type="password",
                    key="reg_pwd_input",
                )
            with col_p2:
                reg_pwd_confirm = st.text_input(
                    "Confirma tu Contraseña:",
                    type="password",
                    key="reg_pwd_confirm_input",
                )

            if st.button("✨ Crear Cuenta y Comenzar →", type="primary", use_container_width=True, key="btn_do_register"):
                ok, msg = register_student_account(reg_user, reg_pwd, reg_pwd_confirm)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    st.stop()


# =====================================================================
# CÁLCULO DE MÉTRICAS GAMIFICADAS DEL USUARIO ACTIVO
# =====================================================================
engine: GoPAESAdaptiveEngine = st.session_state.engine
profile = engine.profile

user_elo = get_profile_elo(profile)
user_wins = get_profile_wins(profile)
user_level = 1 + (engine.total_questions_answered // 8) + (user_wins // 2)
league_title, league_bg, league_fg = get_league_info(user_elo)

leaderboard_data = get_global_leaderboard()
user_rank_entry = next((item for item in leaderboard_data if item["username"].lower() == profile.username.lower()), None)
user_rank_str = f"#{user_rank_entry['rank']}" if user_rank_entry else "#-"
user_initials = (profile.username[:2]).upper()

# Misiones / Unidades superadas (dominio >= 55% o al menos 1 pregunta respondida en la unidad)
missions_done = sum(
    1 for ax in ALL_AXES if engine.axes_state[ax].mastery_score >= 0.55 or engine.axes_state[ax].total_seen >= 2
)

# Estado discreto de servicios en línea
prov_active, resolved_key, _ = GoPAESLLMCoach.resolve_credentials()
is_ia_online, _ = GoPAESLLMCoach.validate_key_format(prov_active, resolved_key)
if hasattr(GoPAESProfileManager, "resolve_supabase_credentials"):
    supa_url, supa_key, _ = GoPAESProfileManager.resolve_supabase_credentials()
else:
    supa_url, supa_key = os.getenv("SUPABASE_URL"), (os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY"))
is_db_online = bool(supa_url and supa_key)


# =====================================================================
# BARRA SUPERIOR DE NAVEGACIÓN ESTILO WEB MODERNA (COMO EN LA IMAGEN)
# =====================================================================
st.markdown(
    f"""
    <div class="gopaes-topbar">
        <div class="gopaes-brand">
            <span class="gopaes-logo-text">GoPAES</span>
            <span class="gopaes-badge-pill">PAES - M1 / M2</span>
            <span style="font-size:0.78rem; color:#64748B; font-weight:600;">
                {'🟢 En línea' if (is_ia_online or is_db_online) else '🟢 Activo'}
            </span>
        </div>
        <div class="gopaes-user-pills">
            <span class="gopaes-stat-pill" title="Racha de días estudiando">🔥 {profile.study_streak}</span>
            <span class="gopaes-stat-pill" title="Victorias en Duelo 1v1">✨ {user_wins}</span>
            <div class="gopaes-avatar-pill">
                <span class="gopaes-avatar-circle">{user_initials}</span>
                <span>{profile.username}</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Menú de Navegación Superior Horizontal Limpio
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns([1.2, 1.5, 1.3, 1.2, 1.4, 1.0])
with nav_col1:
    if st.button(
        "🏠 Inicio",
        type="primary" if st.session_state.nav_section == "DASHBOARD" else "secondary",
        use_container_width=True,
    ):
        st.session_state.nav_section = "DASHBOARD"
        st.rerun()
with nav_col2:
    if st.button(
        "📖 Modo Historia / Guías",
        type="primary" if st.session_state.nav_section in ("GUIDES_M1", "GUIDES_M2") else "secondary",
        use_container_width=True,
    ):
        st.session_state.selected_guide_axis = None
        st.session_state.nav_section = "GUIDES_M1"
        st.rerun()
with nav_col3:
    if st.button(
        "⚔️ Duelo 1v1",
        type="primary" if st.session_state.nav_section == "DUEL_1V1" else "secondary",
        use_container_width=True,
    ):
        st.session_state.nav_section = "DUEL_1V1"
        st.rerun()
with nav_col4:
    if st.button(
        "🏆 Ranking",
        type="primary" if st.session_state.nav_section == "RANKING" else "secondary",
        use_container_width=True,
    ):
        st.session_state.nav_section = "RANKING"
        st.rerun()
with nav_col5:
    if st.button(
        "📝 Ensayos PAES",
        type="primary" if st.session_state.nav_section == "EXAMS" else "secondary",
        use_container_width=True,
    ):
        st.session_state.exam_subphase = "CONFIG"
        st.session_state.nav_section = "EXAMS"
        st.rerun()
with nav_col6:
    if st.button("🔒 Salir", type="secondary", use_container_width=True):
        logout_profile()


# Barra lateral compacta de estado por unidad
with st.sidebar:
    st.markdown(f"## 🚀 GoPAES • **{profile.username}**")
    st.caption(f"{league_title} • **{user_elo} ELO**")
    st.caption("🟢 **Coaching IA:** En línea" if is_ia_online else "🟢 **Coaching IA:** Activo")
    st.caption("🟢 **Nube GoPAES:** En línea" if is_db_online else "🟡 **Almacenamiento:** Local")
    st.divider()
    st.markdown("### 🧠 Dominio en las 4 Unidades")
    adaptive_probs = engine.compute_sampling_probabilities(mode="ADAPTIVE")
    rows = []
    for axis in ALL_AXES:
        st_axis = engine.axes_state[axis]
        rows.append({
            "Unidad": AXIS_LABELS[axis],
            "Dominio": f"{round(st_axis.mastery_score * 100)}%",
            "Peso IA": f"{round(adaptive_probs[axis] * 100, 1)}%",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# =====================================================================
# FUNCIONES DE CONSOLIDACIÓN DE LAS 4 GUÍAS POR UNIDAD (M1 Y M2)
# =====================================================================
def get_consolidated_unit_guide(exam_target: ExamType, axis: ThematicAxis) -> DEMREExhaustiveGuide:
    guides_by_axis = get_exhaustive_guides_by_exam(exam_target)
    axis_list = guides_by_axis.get(axis, [])
    if len(axis_list) == 1:
        return axis_list[0]

    base = axis_list[0]
    all_formulas, all_recipes, all_traps, all_exercises, md_parts = [], [], [], [], []
    for g in axis_list:
        md_parts.append(g.theoretical_framework_md)
        all_formulas.extend(g.key_formulas)
        all_recipes.extend(g.resolution_recipe_steps)
        all_traps.extend(g.common_demre_traps)
        all_exercises.extend(g.interleaved_exercises)

    return base.model_copy(
        update={
            "guide_id": f"GUIDE-{exam_target}-{axis}",
            "unit_title": f"{UNIT_NUMBER_LABELS[axis]} (PAES {exam_target})",
            "theoretical_framework_md": "\n\n---\n\n".join(md_parts),
            "key_formulas": all_formulas,
            "resolution_recipe_steps": all_recipes,
            "common_demre_traps": all_traps,
            "interleaved_exercises": all_exercises,
        }
    )


def get_unit_questions_from_store(
    vector_store: GoPAESVectorStore,
    exam: ExamType,
    axis: ThematicAxis,
    num_questions: int,
    exclude_ids: list[str] | None = None,
) -> list[DEMREQuestionNode]:
    excluded = set(exclude_ids or [])
    unseen = vector_store.query_by_axis_and_exam(
        exam=exam, axis=axis, exclude_ids=list(excluded), diagnostic_only=False
    )
    all_axis = vector_store.query_by_axis_and_exam(
        exam=exam, axis=axis, exclude_ids=[], diagnostic_only=False
    )
    combined: list[DEMREQuestionNode] = []
    for q in unseen + all_axis:
        if q.node_id not in [c.node_id for c in combined]:
            combined.append(q)
        if len(combined) >= num_questions:
            break
    return combined[:num_questions]


def render_question_card(question: DEMREQuestionNode, step_num: int, total_steps: int, badge_text: str):
    col_badge, col_source = st.columns([2, 2])
    with col_badge:
        st.markdown(f"#### {badge_text} • Pregunta {step_num} de {total_steps}")
    with col_source:
        st.markdown(
            f"<div style='text-align:right; color:#64748B; font-size:0.9rem;'>"
            f"📌 <b>PAES {question.exam}</b> | Unidad: <b>{AXIS_LABELS[question.thematic_axis]}</b> "
            f"({question.subtopic_name})</div>",
            unsafe_allow_html=True,
        )

    st.markdown(f"**Enunciado Oficial (DEMRE #{question.question_number}):**")
    st.write(question.stem_text)
    st.latex(question.stem_latex)

    if question.figure_svg:
        st.markdown("**Figura Geométrica Asociada:**")
        st.markdown(question.figure_svg, unsafe_allow_html=True)

    st.markdown("**Alternativas Oficiales:**")
    for opt in question.options:
        col_key, col_formula = st.columns([1, 11])
        with col_key:
            st.markdown(f"### `{opt.key})`")
        with col_formula:
            st.latex(opt.latex_content)


# =====================================================================
# VISTA PRINCIPAL: INICIO / DASHBOARD GAMIFICADO GOPAES (FIEL A LA IMAGEN)
# =====================================================================
if st.session_state.nav_section == "DASHBOARD":
    # 1. HERO BANNER AZUL / ÍNDIGO GAMIFICADO
    st.markdown(
        f"""
        <div class="gopaes-hero">
            <div>
                <div class="gopaes-hero-tag">✨ Preuniversitario Gamificado GoPAES</div>
                <h1 class="gopaes-hero-title">¡Hola, {profile.username}!</h1>
                <p class="gopaes-hero-sub">
                    ¿Qué desafío vamos a superar hoy? Resuelve ensayos personalizados,
                    refuerza tus debilidades en las 4 Unidades y compite en duelos 1v1.
                </p>
            </div>
            <div class="gopaes-hero-stats">
                <div class="gopaes-glass-box">
                    <div class="gopaes-glass-label">Nivel</div>
                    <div class="gopaes-glass-val">{user_level}</div>
                </div>
                <div class="gopaes-glass-box">
                    <div class="gopaes-glass-label">🔥 Racha</div>
                    <div class="gopaes-glass-val">{profile.study_streak} d</div>
                </div>
                <div class="gopaes-glass-box">
                    <div class="gopaes-glass-label">Puntaje ELO</div>
                    <div class="gopaes-glass-val">{user_elo}</div>
                </div>
                <div class="gopaes-glass-box">
                    <div class="gopaes-glass-label">Ranking</div>
                    <div class="gopaes-glass-val">{user_rank_str}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. FRANJA DE DIAGNÓSTICO DE RENDIMIENTO
    with st.container(border=True):
        col_diag_text, col_diag_btn = st.columns([3.4, 1.2])
        with col_diag_text:
            st.markdown(
                """
                <div style="display:flex; align-items:center; gap:16px;">
                    <div style="background:#DBEAFE; color:#2563EB; width:48px; height:48px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.4rem; flex-shrink:0;">
                        🎯
                    </div>
                    <div>
                        <div style="color:#2563EB; font-size:0.8rem; font-weight:700;">✨ Diagnóstico de Rendimiento</div>
                        <div style="font-size:1.1rem; font-weight:800; color:#0F172A; margin:2px 0;">Descubre tus fortalezas y oportunidades de mejora</div>
                        <div style="font-size:0.88rem; color:#475569;">
                            Resuelve tus primeros ejercicios para que GoPAES analice tus respuestas reales y detecte en qué unidades te conviene enfocar tu estudio.
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_diag_btn:
            st.write("")
            if st.button("Configurar primer ensayo →", type="primary", use_container_width=True, key="hero_diag_btn"):
                if not profile.diagnostic_completed:
                    st.session_state.diag_idx = 0
                    st.session_state.nav_section = "DIAGNOSTIC"
                else:
                    st.session_state.exam_subphase = "CONFIG"
                    st.session_state.nav_section = "EXAMS"
                st.rerun()

    st.write("")
    st.markdown("### Modos Principales")
    st.caption("Elige cómo quieres practicar y competir hoy")

    # 3. LAS 3 TARJETAS DE MODOS PRINCIPALES (Modo Historia/Guías | Duelo 1v1 en Vivo | Ranking y Ligas)
    col_m1, col_m2, col_m3 = st.columns(3)

    # Tarjeta 1: Modo Historia y Guías por Unidad
    with col_m1:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="mode-card-header">
                    <div class="mode-icon-box" style="background:#EFF6FF; color:#2563EB;">📖</div>
                    <span class="mode-pill" style="background:#F1F5F9; color:#334155;">Ruta Adaptativa</span>
                </div>
                <h4 style="margin:0 0 6px 0; font-size:1.2rem; font-weight:800;">Modo Historia y Guías</h4>
                <p style="font-size:0.88rem; color:#475569; min-height:54px; margin-bottom:12px;">
                    Tu aventura continúa. Avanza por las 4 Unidades DEMRE, domina fórmulas y recetas paso a paso y prepárate para la PAES.
                </p>
                <div style="display:flex; justify-content:space-between; font-size:0.82rem; font-weight:700; color:#334155; margin-bottom:4px;">
                    <span>Progreso de Unidades</span>
                    <span>{missions_done}/4 unidades</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(missions_done / 4.0)
            st.write("")
            if st.button("Continuar historia →", type="primary", use_container_width=True, key="card_btn_story"):
                st.session_state.selected_guide_axis = None
                st.session_state.nav_section = "GUIDES_M1"
                st.rerun()

    # Tarjeta 2: Duelo 1v1 en Vivo
    with col_m2:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="mode-card-header">
                    <div class="mode-icon-box" style="background:#EEF2FF; color:#4F46E5;">⚔️</div>
                    <span class="mode-pill" style="background:{league_bg}; color:{league_fg};">{league_title}</span>
                </div>
                <h4 style="margin:0 0 6px 0; font-size:1.2rem; font-weight:800;">Duelo 1v1 en Vivo</h4>
                <p style="font-size:0.88rem; color:#475569; min-height:54px; margin-bottom:12px;">
                    ¿Crees que puedes ganar? Desafía a otro estudiante en 5 preguntas sincrónicas y sube tu rating ELO.
                </p>
                <div class="elo-inner-box">
                    <div>
                        <div style="font-size:0.75rem; color:#64748B; font-weight:600;">Tu Rating</div>
                        <div style="font-size:1.15rem; font-weight:800; color:#0F172A;">{user_elo} ELO</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:0.75rem; color:#64748B; font-weight:600;">Victorias</div>
                        <div style="font-size:1.15rem; font-weight:800; color:#059669;">{user_wins}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Jugar duelo 1v1 ⚔️", type="primary", use_container_width=True, key="card_btn_duel"):
                st.session_state.duel_state["phase"] = "LOBBY"
                st.session_state.nav_section = "DUEL_1V1"
                st.rerun()

    # Tarjeta 3: Ranking y Ligas
    with col_m3:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="mode-card-header">
                    <div class="mode-icon-box" style="background:#FEF3C7; color:#D97706;">🏆</div>
                    <span class="mode-pill" style="background:#F1F5F9; color:#334155;">Semanal</span>
                </div>
                <h4 style="margin:0 0 6px 0; font-size:1.2rem; font-weight:800;">Ranking y Ligas</h4>
                <p style="font-size:0.88rem; color:#475569; min-height:54px; margin-bottom:12px;">
                    Escala posiciones en la liga compartida, compite con otros postulantes y llega a la Liga Diamante.
                </p>
                <div class="elo-inner-box">
                    <span style="font-size:0.82rem; color:#64748B; font-weight:600;">Tu posición:</span>
                    <span style="font-size:1rem; font-weight:800; color:#0F172A;">Puesto {user_rank_str} ({league_title})</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Ver ranking global ›", type="secondary", use_container_width=True, key="card_btn_rank"):
                st.session_state.nav_section = "RANKING"
                st.rerun()

    st.write("")

    # 4. SECCIÓN: ENSAYOS Y PRÁCTICA POR ASIGNATURA (M1 Y M2)
    col_sec_head, col_sec_btn = st.columns([3, 1.2])
    with col_sec_head:
        st.markdown("### Ensayos y Práctica por Asignatura")
        st.caption("Configura un ensayo con temporizador a medida o practica las baterías completas por unidad")
    with col_sec_btn:
        if st.button("🎚️ Configurar Ensayo a Medida", type="primary", use_container_width=True):
            st.session_state.exam_subphase = "CONFIG"
            st.session_state.nav_section = "EXAMS"
            st.rerun()

    # Franja de Ensayos Personalizables rápidos (10 preguntas M1 / 10 preguntas M2)
    with st.container(border=True):
        c_strip_info, c_strip_m1, c_strip_m2 = st.columns([2.8, 1, 1])
        with c_strip_info:
            st.markdown(
                """
                <div style="display:flex; align-items:center; gap:14px;">
                    <div style="background:#DCFCE7; color:#15803D; width:42px; height:42px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.2rem; flex-shrink:0;">
                        🎚️
                    </div>
                    <div>
                        <div style="font-size:1.02rem; font-weight:800; color:#0F172A;">Ensayos Personalizables: Duración y Preguntas Sincronizadas</div>
                        <div style="font-size:0.85rem; color:#475569;">
                            Selecciona la cantidad de ejercicios o inicia un ensayo rápido de 10 preguntas. Nuestro selector inteligente prioriza preguntas nuevas y refuerza tus debilidades.
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_strip_m1:
            st.write("")
            if st.button("Ensayo M1 (10 preg.)", type="secondary", use_container_width=True):
                q_m1 = engine.build_exam_question_queue(
                    vector_store=st.session_state.vector_store,
                    exam="M1",
                    num_questions=10,
                    mode="ADAPTIVE",
                    asked_ids=st.session_state.asked_ids,
                )
                st.session_state.exam_config = {
                    "exam": "M1",
                    "num_questions": len(q_m1),
                    "timed_mode": True,
                    "allocated_seconds": len(q_m1) * OFFICIAL_SECONDS_PER_QUESTION["M1"],
                    "selection_mode": "ADAPTIVE",
                    "focus_axis": None,
                }
                st.session_state.exam_queue = q_m1
                st.session_state.exam_history = []
                st.session_state.exam_subphase = "ACTIVE_RUN"
                st.session_state.nav_section = "EXAMS"
                st.rerun()
        with c_strip_m2:
            st.write("")
            if st.button("Ensayo M2 (10 preg.)", type="secondary", use_container_width=True):
                q_m2 = engine.build_exam_question_queue(
                    vector_store=st.session_state.vector_store,
                    exam="M2",
                    num_questions=10,
                    mode="ADAPTIVE",
                    asked_ids=st.session_state.asked_ids,
                )
                st.session_state.exam_config = {
                    "exam": "M2",
                    "num_questions": len(q_m2),
                    "timed_mode": True,
                    "allocated_seconds": len(q_m2) * OFFICIAL_SECONDS_PER_QUESTION["M2"],
                    "selection_mode": "ADAPTIVE",
                    "focus_axis": None,
                }
                st.session_state.exam_queue = q_m2
                st.session_state.exam_history = []
                st.session_state.exam_subphase = "ACTIVE_RUN"
                st.session_state.nav_section = "EXAMS"
                st.rerun()

    # Tarjetas grandes Matemática 1 y Matemática 2
    col_mat1, col_mat2 = st.columns(2)
    m1_count = len(st.session_state.vector_store.get_all_nodes(exam="M1"))
    m2_count = len(st.session_state.vector_store.get_all_nodes(exam="M2"))

    with col_mat1:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="mode-card-header">
                    <div class="mode-icon-box" style="background:#EFF6FF; color:#2563EB;">📘</div>
                    <span class="mode-pill" style="background:#F1F5F9; color:#0F172A;">PAES M1</span>
                </div>
                <h3 style="margin:0 0 6px 0; font-size:1.35rem; font-weight:800;">Matemática 1</h3>
                <p style="font-size:0.9rem; color:#475569; margin-bottom:14px;">
                    Números, Álgebra y Funciones, Geometría y Probabilidad. Base obligatoria para todas las carreras.
                </p>
                <div style="display:flex; justify-content:space-between; font-size:0.84rem; color:#64748B; border-top:1px solid #F1F5F9; padding-top:12px; margin-bottom:14px;">
                    <span>{m1_count} ejercicios oficiales disponibles</span>
                    <span style="color:#0F172A; font-weight:700;">Explicación paso a paso en LaTeX</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            b_m1_left, b_m1_right = st.columns(2)
            with b_m1_left:
                if st.button("📖 Guías M1 (4 Unidades)", type="secondary", use_container_width=True):
                    st.session_state.selected_guide_axis = None
                    st.session_state.nav_section = "GUIDES_M1"
                    st.rerun()
            with b_m1_right:
                if st.button("Practicar M1 →", type="primary", use_container_width=True):
                    st.session_state.exam_config["exam"] = "M1"
                    st.session_state.exam_subphase = "CONFIG"
                    st.session_state.nav_section = "EXAMS"
                    st.rerun()

    with col_mat2:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="mode-card-header">
                    <div class="mode-icon-box" style="background:#F3E8FF; color:#7E22CE;">✨</div>
                    <span class="mode-pill" style="background:#F1F5F9; color:#0F172A;">PAES M2</span>
                </div>
                <h3 style="margin:0 0 6px 0; font-size:1.35rem; font-weight:800;">Matemática 2</h3>
                <p style="font-size:0.9rem; color:#475569; margin-bottom:14px;">
                    Reales, logaritmos, matemática financiera, sistemas paramétricos, homotecia, trigonometría y combinatoria.
                </p>
                <div style="display:flex; justify-content:space-between; font-size:0.84rem; color:#64748B; border-top:1px solid #F1F5F9; padding-top:12px; margin-bottom:14px;">
                    <span>{m2_count} ejercicios oficiales disponibles</span>
                    <span style="color:#0F172A; font-weight:700;">Explicación paso a paso en LaTeX</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            b_m2_left, b_m2_right = st.columns(2)
            with b_m2_left:
                if st.button("📕 Guías M2 (4 Unidades)", type="secondary", use_container_width=True):
                    st.session_state.selected_guide_axis = None
                    st.session_state.nav_section = "GUIDES_M2"
                    st.rerun()
            with b_m2_right:
                if st.button("Practicar M2 →", type="primary", use_container_width=True):
                    st.session_state.exam_config["exam"] = "M2"
                    st.session_state.exam_subphase = "CONFIG"
                    st.session_state.nav_section = "EXAMS"
                    st.rerun()

    st.write("")
    # 5. RESUMEN DE DOMINIO EN LAS 4 UNIDADES OFICIALES
    with st.container(border=True):
        st.markdown("#### 📊 Tu Progreso por Unidad DEMRE")
        cols_u = st.columns(4)
        for idx_u, axis in enumerate(ALL_AXES):
            st_ax = engine.axes_state[axis]
            dom_pct = round(st_ax.mastery_score * 100, 1)
            with cols_u[idx_u]:
                st.markdown(f"**{UNIT_ICONS[axis]} {AXIS_LABELS[axis]}**")
                st.caption(f"Dominio: **{dom_pct}%** • Precisión: `{st_ax.net_accuracy}%`")
                st.progress(min(1.0, st_ax.mastery_score))


# =====================================================================
# SECCIÓN MULTIJUGADOR: DUELO 1V1 EN VIVO (SALAS COMPARTIDAS + MATCHMAKING)
# =====================================================================
elif st.session_state.nav_section == "DUEL_1V1":
    ds = st.session_state.duel_state

    if ds["phase"] == "LOBBY":
        st.markdown(
            f"""
            <div class="gopaes-hero" style="padding: 26px 32px;">
                <div>
                    <div class="gopaes-hero-tag">⚔️ Arena Multijugador GoPAES • {league_title}</div>
                    <h2 class="gopaes-hero-title" style="font-size:1.95rem;">Duelo 1v1 en Vivo</h2>
                    <p class="gopaes-hero-sub">
                        Compite en 5 preguntas oficiales PAES contra otro estudiante en tiempo real,
                        crea una sala con código para desafiar a un amigo o acepta un duelo abierto del lobby.
                    </p>
                </div>
                <div class="gopaes-hero-stats">
                    <div class="gopaes-glass-box">
                        <div class="gopaes-glass-label">Tu ELO</div>
                        <div class="gopaes-glass-val">{user_elo}</div>
                    </div>
                    <div class="gopaes-glass-box">
                        <div class="gopaes-glass-label">Victorias</div>
                        <div class="gopaes-glass-val">{user_wins}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_quick, col_room = st.columns(2)

        # Opción A: Emparejamiento Rápido 1v1 en tu Liga
        with col_quick:
            with st.container(border=True):
                st.subheader("⚡ Emparejamiento Rápido 1v1")
                st.write(
                    "Busca automáticamente un rival de tu liga o un desafío abierto en la nube para competir ahora mismo en 5 preguntas:"
                )
                duel_exam: ExamType = st.radio(
                    "Modalidad del Duelo:",
                    options=["M1", "M2"],
                    horizontal=True,
                    format_func=lambda x: "📘 PAES M1 (Obligatoria)" if x == "M1" else "📕 PAES M2 (Electiva)",
                    key="duel_quick_exam_radio",
                )

                if st.button("⚔️ Buscar Rival y Jugar 1v1 Ahora", type="primary", use_container_width=True):
                    # Seleccionar rival de nivel cercano en el Ranking Global
                    candidates = [p for p in leaderboard_data if p["username"].lower() != profile.username.lower()]
                    candidates.sort(key=lambda x: abs(x["elo"] - user_elo))
                    chosen_opp = candidates[0] if candidates else {"username": "Matias_DEMRE", "elo": 1020}

                    duel_qs = engine.build_exam_question_queue(
                        vector_store=st.session_state.vector_store,
                        exam=duel_exam,
                        num_questions=5,
                        mode="GENERAL_STANDARD",
                        asked_ids=st.session_state.asked_ids,
                    )
                    # Simular desempeño calibrado del rival según su ELO y dificultad de cada pregunta
                    rng = random.Random(f"{profile.username}_{chosen_opp['username']}_{len(st.session_state.asked_ids)}")
                    opp_prob = min(0.88, max(0.35, 0.55 + (chosen_opp["elo"] - 1000) / 1000.0))
                    opp_ans = [rng.random() < opp_prob for _ in duel_qs]

                    st.session_state.duel_state = {
                        "phase": "ACTIVE_DUEL",
                        "room_code": f"LIVE-{random.randint(1000, 9999)}",
                        "exam": duel_exam,
                        "opponent_name": chosen_opp["username"],
                        "opponent_elo": chosen_opp["elo"],
                        "opponent_answers": opp_ans,
                        "questions": duel_qs,
                        "player_history": [],
                        "elo_delta": 0,
                        "is_room_creator": False,
                    }
                    st.rerun()

        # Opción B: Crear o Unirse a una Sala Multijugador con Código entre Amigos
        with col_room:
            with st.container(border=True):
                st.subheader("🏠 Sala de Duelo con Código (Contra un Amigo)")
                st.write(
                    "Crea una sala compartida en la nube y pásale el código a tu amigo para que ambos resuelvan las **mismas 5 preguntas**:"
                )
                c_create, c_join = st.columns(2)
                with c_create:
                    if st.button("➕ Crear Sala 1v1", type="secondary", use_container_width=True):
                        code = f"GOPAES-{random.randint(100, 999)}"
                        room_exam = st.session_state.get("duel_quick_exam_radio", "M1")
                        duel_qs = engine.build_exam_question_queue(
                            vector_store=st.session_state.vector_store,
                            exam=room_exam,
                            num_questions=5,
                            mode="GENERAL_STANDARD",
                            asked_ids=[],
                        )
                        rooms = load_shared_duel_rooms()
                        rooms.append({
                            "room_code": code,
                            "creator": profile.username,
                            "creator_elo": user_elo,
                            "exam": room_exam,
                            "question_ids": [q.node_id for q in duel_qs],
                            "creator_score": None,
                            "challenger": None,
                            "challenger_score": None,
                            "created_at": datetime.date.today().isoformat(),
                        })
                        save_shared_duel_rooms(rooms)

                        st.session_state.duel_state = {
                            "phase": "ACTIVE_DUEL",
                            "room_code": code,
                            "exam": room_exam,
                            "opponent_name": "Esperando Amigo (Sala " + code + ")",
                            "opponent_elo": user_elo,
                            "opponent_answers": [True, False, True, True, False],
                            "questions": duel_qs,
                            "player_history": [],
                            "elo_delta": 0,
                            "is_room_creator": True,
                        }
                        st.rerun()

                with c_join:
                    input_code = st.text_input(
                        "Código de Sala:",
                        placeholder="Ej: GOPAES-482",
                        label_visibility="collapsed",
                        key="join_room_code_input",
                    )
                    if st.button("🔑 Unirme por Código", type="primary", use_container_width=True):
                        clean_code = input_code.strip().upper()
                        rooms = load_shared_duel_rooms()
                        found_room = next((r for r in rooms if r.get("room_code", "").upper() == clean_code), None)
                        if not found_room:
                            st.error(f"No se encontró la sala '{clean_code}'. Verifica el código.")
                        else:
                            all_map = {n.node_id: n for n in st.session_state.vector_store.get_all_nodes()}
                            q_objs = [all_map[qid] for qid in found_room.get("question_ids", []) if qid in all_map]
                            if not q_objs:
                                q_objs = engine.build_exam_question_queue(
                                    st.session_state.vector_store, found_room.get("exam", "M1"), 5, "GENERAL_STANDARD", []
                                )
                            creator_sc = found_room.get("creator_score")
                            c_ans = [i < (creator_sc if creator_sc is not None else 3) for i in range(len(q_objs))]
                            st.session_state.duel_state = {
                                "phase": "ACTIVE_DUEL",
                                "room_code": found_room["room_code"],
                                "exam": found_room.get("exam", "M1"),
                                "opponent_name": found_room.get("creator", "Rival"),
                                "opponent_elo": found_room.get("creator_elo", 1000),
                                "opponent_answers": c_ans,
                                "questions": q_objs,
                                "player_history": [],
                                "elo_delta": 0,
                                "is_room_creator": False,
                            }
                            st.rerun()

        # Lista de Salas / Desafíos Abiertos en la Nube
        rooms_list = load_shared_duel_rooms()
        open_rooms = [r for r in reversed(rooms_list) if r.get("creator") != profile.username][:5]
        if open_rooms:
            with st.container(border=True):
                st.markdown("#### 🌐 Desafíos 1v1 Abiertos por Otros Estudiantes")
                for r in open_rooms:
                    c_r1, c_r2, c_r3, c_r4 = st.columns([1.5, 1.5, 1.5, 1.2])
                    c_r1.markdown(f"**Sala:** `{r['room_code']}`")
                    c_r2.markdown(f"👤 **{r['creator']}** (`{r.get('creator_elo', 1000)} ELO`)")
                    c_r3.markdown(
                        f"📘 PAES **{r.get('exam', 'M1')}** • Puntaje a batir: "
                        f"**{r['creator_score'] if r.get('creator_score') is not None else '?'}/5**"
                    )
                    with c_r4:
                        if st.button("⚔️ Aceptar Duelo", key=f"accept_room_{r['room_code']}", use_container_width=True):
                            all_map = {n.node_id: n for n in st.session_state.vector_store.get_all_nodes()}
                            q_objs = [all_map[qid] for qid in r.get("question_ids", []) if qid in all_map]
                            if not q_objs:
                                q_objs = engine.build_exam_question_queue(
                                    st.session_state.vector_store, r.get("exam", "M1"), 5, "GENERAL_STANDARD", []
                                )
                            c_sc = r.get("creator_score") if r.get("creator_score") is not None else 3
                            c_ans = [i < c_sc for i in range(len(q_objs))]
                            st.session_state.duel_state = {
                                "phase": "ACTIVE_DUEL",
                                "room_code": r["room_code"],
                                "exam": r.get("exam", "M1"),
                                "opponent_name": r["creator"],
                                "opponent_elo": r.get("creator_elo", 1000),
                                "opponent_answers": c_ans,
                                "questions": q_objs,
                                "player_history": [],
                                "elo_delta": 0,
                                "is_room_creator": False,
                            }
                            st.rerun()

    elif ds["phase"] == "ACTIVE_DUEL":
        step = len(ds["player_history"])
        total_duel_q = len(ds["questions"])

        player_pts = sum(1 for h in ds["player_history"] if h["state"] == "CORRECT")
        opp_pts = sum(1 for b in ds["opponent_answers"][:step] if b)

        # Marcador 1v1 en Vivo en la parte superior
        with st.container(border=True):
            c_p1, c_vs, c_p2 = st.columns([2, 1, 2])
            with c_p1:
                st.markdown(
                    f"### 🟦 {profile.username} (`{user_elo} ELO`)\n"
                    f"#### Puntaje: **{player_pts} / {total_duel_q}**"
                )
            with c_vs:
                st.markdown(
                    f"<div style='text-align:center; padding-top:10px;'>"
                    f"<span style='background:#EEF2FF; color:#4F46E5; padding:6px 14px; border-radius:999px; font-weight:800;'>"
                    f"Sala {ds['room_code']}</span><br><h3 style='margin:6px 0;'>⚔️ VS</h3></div>",
                    unsafe_allow_html=True,
                )
            with c_p2:
                st.markdown(
                    f"<div style='text-align:right;'>"
                    f"<h3>🟥 {ds['opponent_name']} (<code>{ds['opponent_elo']} ELO</code>)</h3>"
                    f"<h4>Puntaje: <b>{opp_pts} / {total_duel_q}</b></h4></div>",
                    unsafe_allow_html=True,
                )

        if step >= total_duel_q:
            # Calcular resultado final y actualizar ELO
            final_opp_pts = sum(1 for b in ds["opponent_answers"][:total_duel_q] if b)
            if player_pts > final_opp_pts:
                outcome = 1.0
                new_wins = user_wins + 1
            elif player_pts == final_opp_pts:
                outcome = 0.5
                new_wins = user_wins
            else:
                outcome = 0.0
                new_wins = user_wins

            delta_elo = calculate_elo_change(user_elo, ds["opponent_elo"], outcome)
            new_elo = max(800, user_elo + delta_elo)
            set_profile_elo_and_wins(profile, new_elo=new_elo, new_wins=new_wins)

            # Si era sala compartida, guardar el puntaje del creador o retador en la nube
            rooms = load_shared_duel_rooms()
            for r in rooms:
                if r.get("room_code") == ds["room_code"]:
                    if ds.get("is_room_creator"):
                        r["creator_score"] = player_pts
                    else:
                        r["challenger"] = profile.username
                        r["challenger_score"] = player_pts
            save_shared_duel_rooms(rooms)

            ds["elo_delta"] = delta_elo
            ds["phase"] = "DUEL_RESULTS"
            st.rerun()

        q_duel: DEMREQuestionNode = ds["questions"][step]
        with st.container(border=True):
            render_question_card(
                question=q_duel,
                step_num=step + 1,
                total_steps=total_duel_q,
                badge_text=f"⚔️ Duelo 1v1 ({ds['exam']})",
            )
            st.divider()
            choice_d = st.radio(
                "Tu respuesta rápida:",
                options=[o.key for o in q_duel.options],
                format_func=lambda k: f"Alternativa {k}",
                horizontal=True,
                key=f"duel_radio_{step}_{q_duel.node_id}",
            )
            if st.button("⚡ Confirmar Respuesta del Duelo", type="primary", use_container_width=True):
                st_res = engine.process_response(q_duel, choice_d, phase_label="Duelo 1v1")
                st.session_state.asked_ids.append(q_duel.node_id)
                ds["player_history"].append({
                    "question": q_duel,
                    "selected_option": choice_d,
                    "state": st_res,
                })
                st.rerun()

    elif ds["phase"] == "DUEL_RESULTS":
        total_duel_q = len(ds["questions"])
        player_pts = sum(1 for h in ds["player_history"] if h["state"] == "CORRECT")
        final_opp_pts = sum(1 for b in ds["opponent_answers"][:total_duel_q] if b)
        delta_elo = ds["elo_delta"]
        sign_str = f"+{delta_elo}" if delta_elo >= 0 else f"{delta_elo}"

        if player_pts > final_opp_pts:
            st.balloons()
            st.success(
                f"🏆 **¡VICTORIA EN EL DUELO 1v1!** Venciste a **{ds['opponent_name']}** por **{player_pts} a {final_opp_pts}**. "
                f"Tu Rating ELO sube en **`{sign_str} ELO`** (Nuevo Rating: **{get_profile_elo(profile)} ELO**)."
            )
        elif player_pts == final_opp_pts:
            st.info(
                f"🤝 **¡EMPATE TÉCNICO!** Igualaste **{player_pts} a {final_opp_pts}** contra **{ds['opponent_name']}**. "
                f"Variación ELO: **`{sign_str} ELO`**."
            )
        else:
            st.error(
                f"⚔️ **Duelo finalizado:** **{ds['opponent_name']}** obtuvo **{final_opp_pts}/{total_duel_q}** y tú obtuviste **{player_pts}/{total_duel_q}**. "
                f"Variación ELO: **`{sign_str} ELO`**. ¡Revisa las explicaciones abajo para la revancha!"
            )

        if ds.get("is_room_creator"):
            st.info(
                f"📢 **Comparte este Código de Sala con tu amigo para que intente superar tu puntaje ({player_pts}/5):**  \n"
                f"### `{ds['room_code']}`"
            )

        c_b1, c_b2 = st.columns(2)
        with c_b1:
            if st.button("⚔️ Jugar Otro Duelo 1v1", type="primary", use_container_width=True):
                ds["phase"] = "LOBBY"
                st.rerun()
        with c_b2:
            if st.button("🏆 Ver mi nueva posición en el Ranking", type="secondary", use_container_width=True):
                ds["phase"] = "LOBBY"
                st.session_state.nav_section = "RANKING"
                st.rerun()

        st.markdown("### 📘 Revisión Paso a Paso de las Preguntas del Duelo")
        for idx_h, item_h in enumerate(ds["player_history"], start=1):
            qd: DEMREQuestionNode = item_h["question"]
            sel_d = item_h["selected_option"]
            st_d = item_h["state"]
            with st.container(border=True):
                if st_d == "CORRECT":
                    st.success(f"**Pregunta {idx_h}:** ✅ Correcta (Marcaste {sel_d})")
                else:
                    st.error(f"**Pregunta {idx_h}:** ❌ Marcaste {sel_d} • Clave Oficial DEMRE: **{qd.correct_option})**")
                st.write(qd.stem_text)
                st.latex(qd.stem_latex)
                explanation = GoPAESLLMCoach.generate_live_latex_explanation(
                    question=qd, selected_option=sel_d, state=st_d
                )
                st.markdown(explanation)


# =====================================================================
# SECCIÓN: RANKING GLOBAL Y LIGAS COMPARTIDAS
# =====================================================================
elif st.session_state.nav_section == "RANKING":
    st.markdown(
        f"""
        <div class="gopaes-hero" style="padding: 26px 32px;">
            <div>
                <div class="gopaes-hero-tag">🏆 Clasificación Oficial GoPAES • Semanal</div>
                <h2 class="gopaes-hero-title" style="font-size:1.95rem;">Ranking Global y Ligas</h2>
                <p class="gopaes-hero-sub">
                    Escala posiciones ganando duelos 1v1 y manteniendo tu racha de estudio diaria.
                    Desafía directamente a cualquier estudiante de la tabla.
                </p>
            </div>
            <div class="gopaes-hero-stats">
                <div class="gopaes-glass-box">
                    <div class="gopaes-glass-label">Tu Puesto</div>
                    <div class="gopaes-glass-val">{user_rank_str}</div>
                </div>
                <div class="gopaes-glass-box">
                    <div class="gopaes-glass-label">Tu ELO</div>
                    <div class="gopaes-glass-val">{user_elo}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Tarjetas de las 4 Ligas
    l1, l2, l3, l4 = st.columns(4)
    with l1:
        with st.container(border=True):
            st.markdown("#### 🥉 Liga Bronce")
            st.caption("Hasta **1079 ELO**")
    with l2:
        with st.container(border=True):
            st.markdown("#### 🥈 Liga Plata")
            st.caption("**1080 – 1219 ELO**")
    with l3:
        with st.container(border=True):
            st.markdown("#### 🥇 Liga Oro")
            st.caption("**1220 – 1399 ELO**")
    with l4:
        with st.container(border=True):
            st.markdown("#### 💎 Liga Diamante")
            st.caption("**1400+ ELO**")

    with st.container(border=True):
        st.subheader("📊 Tabla de Posiciones en Vivo")
        for row_item in leaderboard_data:
            is_me = row_item["username"].lower() == profile.username.lower()
            lg_name, lg_bg, lg_fg = get_league_info(row_item["elo"])
            c_pos, c_user, c_lg, c_elo, c_stats, c_act = st.columns([0.7, 2.0, 1.5, 1.2, 1.8, 1.3])

            medal = "🥇" if row_item["rank"] == 1 else ("🥈" if row_item["rank"] == 2 else ("🥉" if row_item["rank"] == 3 else f"#{row_item['rank']}"))
            c_pos.markdown(f"### {medal}")
            c_user.markdown(
                f"**{row_item['username']}** {' 👈 *(Tú)*' if is_me else ''}"
            )
            c_lg.markdown(
                f"<span style='background:{lg_bg}; color:{lg_fg}; padding:4px 10px; border-radius:999px; font-size:0.78rem; font-weight:700;'>"
                f"{lg_name}</span>",
                unsafe_allow_html=True,
            )
            c_elo.markdown(f"**`{row_item['elo']} ELO`**")
            c_stats.caption(f"⚔️ {row_item['wins']} victorias • 🔥 {row_item['streak']}d")
            with c_act:
                if not is_me:
                    if st.button("⚔️ Desafiar", key=f"chal_rank_{row_item['username']}", use_container_width=True):
                        duel_qs = engine.build_exam_question_queue(
                            vector_store=st.session_state.vector_store,
                            exam="M1",
                            num_questions=5,
                            mode="GENERAL_STANDARD",
                            asked_ids=st.session_state.asked_ids,
                        )
                        rng = random.Random(f"challenge_{profile.username}_{row_item['username']}")
                        opp_prob = min(0.88, max(0.35, 0.55 + (row_item["elo"] - 1000) / 1000.0))
                        opp_ans = [rng.random() < opp_prob for _ in duel_qs]
                        st.session_state.duel_state = {
                            "phase": "ACTIVE_DUEL",
                            "room_code": f"VS-{random.randint(100, 999)}",
                            "exam": "M1",
                            "opponent_name": row_item["username"],
                            "opponent_elo": row_item["elo"],
                            "opponent_answers": opp_ans,
                            "questions": duel_qs,
                            "player_history": [],
                            "elo_delta": 0,
                            "is_room_creator": False,
                        }
                        st.session_state.nav_section = "DUEL_1V1"
                        st.rerun()


# =====================================================================
# SECCIÓN: DIAGNÓSTICO DE CALIBRACIÓN EN LAS 4 UNIDADES
# =====================================================================
elif st.session_state.nav_section == "DIAGNOSTIC":
    st.title("🎯 Diagnóstico de Rendimiento en las 4 Unidades GoPAES")
    st.write(
        "Responde estas preguntas ancla del DEMRE (una por cada unidad: **Números**, **Álgebra y Funciones**, "
        "**Geometría** y **Probabilidad y Estadística**) o usa **'Dejar en blanco'** para calibrar tu perfil."
    )

    diag_qs: list[DEMREQuestionNode] = st.session_state.diag_questions
    idx: int = st.session_state.diag_idx

    if idx >= len(diag_qs):
        st.success("🎉 **¡Diagnóstico completado y guardado en tu cuenta!**")
        if st.button("🏠 Volver al Inicio Actualizado →", type="primary"):
            st.session_state.nav_section = "DASHBOARD"
            st.rerun()
    else:
        current_q = diag_qs[idx]
        with st.container(border=True):
            render_question_card(
                question=current_q,
                step_num=idx + 1,
                total_steps=len(diag_qs),
                badge_text="🎯 Calibración GoPAES",
            )
            st.divider()
            selected_choice = st.radio(
                "Elige una alternativa:",
                options=[o.key for o in current_q.options],
                format_func=lambda k: f"Alternativa {k}",
                horizontal=True,
                key=f"diag_radio_{current_q.node_id}",
            )

            col_submit, col_omit = st.columns([1, 1])
            with col_submit:
                if st.button("✅ Confirmar Alternativa", type="primary", use_container_width=True):
                    engine.process_response(current_q, selected_choice, phase_label="Diagnóstico")
                    st.session_state.asked_ids.append(current_q.node_id)
                    if idx + 1 >= len(diag_qs):
                        engine.mark_diagnostic_completed()
                    st.session_state.diag_idx += 1
                    st.rerun()
            with col_omit:
                if st.button("🏳️ Dejar en blanco (Declarar Vacío de Conocimiento)", use_container_width=True):
                    engine.process_response(current_q, "OMIT", phase_label="Diagnóstico")
                    st.session_state.asked_ids.append(current_q.node_id)
                    if idx + 1 >= len(diag_qs):
                        engine.mark_diagnostic_completed()
                    st.session_state.diag_idx += 1
                    st.rerun()


# =====================================================================
# SECCIÓN: MODO HISTORIA / GUÍAS POR MATERIA (4 UNIDADES DEL DASHBOARD)
# =====================================================================
elif st.session_state.nav_section in ("GUIDES_M1", "GUIDES_M2"):
    exam_target: ExamType = "M1" if st.session_state.nav_section == "GUIDES_M1" else "M2"
    badge_color = "#1d4ed8" if exam_target == "M1" else "#9333ea"
    exam_title = (
        "PAES M1 (Competencia Matemática 1 • Obligatoria)"
        if exam_target == "M1"
        else "PAES M2 (Competencia Matemática 2 • Electiva Científica)"
    )

    col_head, col_switch_exam = st.columns([3, 1.2])
    with col_head:
        st.title(f"{'📘' if exam_target == 'M1' else '📕'} Modo Historia y Guías por Unidad • {exam_title}")
    with col_switch_exam:
        other_exam = "M2" if exam_target == "M1" else "M1"
        if st.button(f"🔄 Cambiar a Guías PAES {other_exam}", type="secondary", use_container_width=True):
            st.session_state.nav_section = f"GUIDES_{other_exam}"
            st.session_state.selected_guide_axis = None
            st.rerun()

    if st.session_state.selected_guide_axis is None:
        st.markdown(
            "Avanza por las **4 Unidades Oficiales DEMRE** (**Números**, **Álgebra y Funciones**, **Geometría**, "
            "**Probabilidad y Estadística**). Elige qué unidad desarrollar y cuántos ejercicios practicar:"
        )
        adaptive_probs = engine.compute_sampling_probabilities(mode="ADAPTIVE")
        col_u1, col_u2 = st.columns(2)
        grid_cols = [col_u1, col_u2, col_u1, col_u2]

        for idx_axis, axis in enumerate(ALL_AXES):
            guide = get_consolidated_unit_guide(exam_target, axis)
            st_axis = engine.axes_state[axis]
            dom_pct = round(st_axis.mastery_score * 100, 1)

            with grid_cols[idx_axis]:
                with st.container(border=True):
                    st.markdown(
                        f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                        f"<h3 style='margin:0;'>{UNIT_ICONS[axis]} {UNIT_NUMBER_LABELS[axis]}</h3>"
                        f"<span style='background:{badge_color}; color:white; padding:3px 12px; border-radius:99px; font-size:0.8rem; font-weight:bold;'>"
                        f"PAES {exam_target}</span></div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(f"📌 {guide.demre_syllabus_reference}")
                    st.markdown(
                        f"**Tu Dominio en {AXIS_LABELS[axis]}:** `{dom_pct}%` | "
                        f"**Precisión Neta:** `{st_axis.net_accuracy}%`"
                    )
                    st.progress(min(1.0, st_axis.mastery_score))
                    st.write(getattr(guide, "short_description", "") or guide.unit_title)

                    c_num, c_open = st.columns([1, 2])
                    with c_num:
                        num_ex_unit = st.number_input(
                            "N° Ejercicios:",
                            min_value=1,
                            max_value=20,
                            value=5,
                            step=1,
                            key=f"menu_num_{exam_target}_{axis}",
                        )
                    with c_open:
                        st.write("")
                        if st.button(
                            f"📖 Abrir Guía ({num_ex_unit} ejercicios) →",
                            type="primary",
                            use_container_width=True,
                            key=f"btn_open_unit_{exam_target}_{axis}",
                        ):
                            st.session_state.selected_guide_axis = axis
                            workout_key = f"{exam_target}_{axis}"
                            st.session_state.unit_custom_workouts[workout_key] = get_unit_questions_from_store(
                                vector_store=st.session_state.vector_store,
                                exam=exam_target,
                                axis=axis,
                                num_questions=int(num_ex_unit),
                                exclude_ids=st.session_state.asked_ids,
                            )
                            st.rerun()
    else:
        active_axis: ThematicAxis = st.session_state.selected_guide_axis
        active_guide = get_consolidated_unit_guide(exam_target, active_axis)
        st_axis_active = engine.axes_state[active_axis]
        dom_active = round(st_axis_active.mastery_score * 100, 1)
        workout_key = f"{exam_target}_{active_axis}"

        col_back, col_unit_badge = st.columns([1.2, 3])
        with col_back:
            if st.button("⬅️ Volver a las 4 Unidades", type="secondary", use_container_width=True):
                st.session_state.selected_guide_axis = None
                st.rerun()
        with col_unit_badge:
            st.markdown(
                f"<div style='text-align:right;'>"
                f"<span style='background:{badge_color}; color:white; padding:5px 14px; border-radius:99px; font-size:0.88rem; font-weight:bold;'>"
                f"{UNIT_NUMBER_LABELS[active_axis]} • Dominio: {dom_active}%</span></div>",
                unsafe_allow_html=True,
            )

        st.header(f"{UNIT_ICONS[active_axis]} {active_guide.unit_title}")
        with st.container(border=True):
            st.markdown(active_guide.theoretical_framework_md)
            st.divider()
            st.markdown("#### 🧮 Formulario y Propiedades Fundamentales ($\\text{LaTeX}$)")
            for f_card in active_guide.key_formulas:
                with st.container(border=True):
                    st.markdown(f"**{f_card.title}**")
                    st.latex(f_card.latex_formula)
                    st.caption(f"💡 *Interpretación DEMRE:* {f_card.explanation}")

            st.divider()
            st.markdown(f"#### 🧑‍🍳 {active_guide.resolution_recipe_title}")
            for recipe_step in active_guide.resolution_recipe_steps:
                st.markdown(f"- ✅ **{recipe_step}**")

            st.divider()
            st.markdown("#### ⚠️ Trampas Frecuentes del DEMRE")
            for trap in active_guide.common_demre_traps:
                st.warning(f"🔎 {trap}")

        st.markdown(f"### ✍️ Ejercicios Guiados de {AXIS_LABELS[active_axis]} (Validación Inmediata)")
        for ex in active_guide.interleaved_exercises:
            with st.container(border=True):
                st.markdown(f"#### 🎯 {ex.title}")
                st.write(ex.stem_text)
                st.latex(ex.stem_latex)
                for opt_k, opt_latex in ex.options.items():
                    c_k, c_lat = st.columns([1, 11])
                    c_k.markdown(f"**`{opt_k})`**")
                    c_lat.latex(opt_latex)

                chosen_ex_opt = st.radio(
                    "Selecciona tu respuesta:",
                    options=list(ex.options.keys()),
                    format_func=lambda k: f"Alternativa {k}",
                    horizontal=True,
                    key=f"interleaved_radio_{ex.exercise_id}",
                )
                if st.button("✅ Comprobar respuesta", type="primary", key=f"btn_check_{ex.exercise_id}"):
                    st.session_state.interleaved_feedback[ex.exercise_id] = chosen_ex_opt

                if ex.exercise_id in st.session_state.interleaved_feedback:
                    user_ans = st.session_state.interleaved_feedback[ex.exercise_id]
                    if user_ans == ex.correct_option:
                        st.success(f"🎉 **¡Respuesta Correcta! Alternativa {ex.correct_option}).**")
                    else:
                        st.error(f"❌ **Incorrecta.** Marcaste {user_ans}), pero la clave es **{ex.correct_option})**.")
                    for s_line in ex.step_by_step_solution:
                        st.markdown(s_line)

        st.markdown(f"### 🏋️ Práctica Personalizada de **{AXIS_LABELS[active_axis]}**")
        current_list: list[DEMREQuestionNode] = st.session_state.unit_custom_workouts.get(workout_key, [])
        default_qty = len(current_list) if current_list else 5

        with st.container(border=True):
            col_slider, col_btn_load = st.columns([3, 2])
            with col_slider:
                desired_qty = st.slider(
                    f"Cantidad de ejercicios de {AXIS_LABELS[active_axis]}:",
                    min_value=1,
                    max_value=20,
                    value=min(20, default_qty),
                    key=f"unit_qty_slider_{workout_key}",
                )
            with col_btn_load:
                st.write("")
                if st.button(
                    f"🔄 Cargar {desired_qty} Ejercicios",
                    type="primary",
                    use_container_width=True,
                    key=f"btn_reload_inline_{workout_key}",
                ):
                    st.session_state.unit_custom_workouts[workout_key] = get_unit_questions_from_store(
                        vector_store=st.session_state.vector_store,
                        exam=exam_target,
                        axis=active_axis,
                        num_questions=int(desired_qty),
                        exclude_ids=st.session_state.asked_ids,
                    )
                    st.rerun()

        if workout_key not in st.session_state.unit_custom_workouts:
            st.session_state.unit_custom_workouts[workout_key] = get_unit_questions_from_store(
                vector_store=st.session_state.vector_store,
                exam=exam_target,
                axis=active_axis,
                num_questions=int(desired_qty),
                exclude_ids=st.session_state.asked_ids,
            )

        workout_questions: list[DEMREQuestionNode] = st.session_state.unit_custom_workouts[workout_key]
        for q_idx, q_node in enumerate(workout_questions, start=1):
            ans_key = f"{workout_key}_{q_node.node_id}"
            with st.container(border=True):
                render_question_card(
                    question=q_node,
                    step_num=q_idx,
                    total_steps=len(workout_questions),
                    badge_text=f"🏋️ {AXIS_LABELS[active_axis]} ({exam_target})",
                )
                chosen_unit_opt = st.radio(
                    "Selecciona tu respuesta:",
                    options=[o.key for o in q_node.options],
                    format_func=lambda k: f"Alternativa {k}",
                    horizontal=True,
                    key=f"unit_q_radio_{ans_key}_{q_idx}",
                )
                col_check, col_omit_u = st.columns(2)
                with col_check:
                    if st.button("✅ Comprobar respuesta", type="primary", use_container_width=True, key=f"btn_u_chk_{ans_key}_{q_idx}"):
                        state_res = engine.process_response(q_node, chosen_unit_opt, phase_label=f"Guía {AXIS_LABELS[active_axis]}")
                        st.session_state.asked_ids.append(q_node.node_id)
                        st.session_state.unit_workout_answers[ans_key] = {"selected": chosen_unit_opt, "state": state_res}
                        st.rerun()
                with col_omit_u:
                    if st.button("🏳️ Dejar en blanco y ver paso a paso", use_container_width=True, key=f"btn_u_omt_{ans_key}_{q_idx}"):
                        state_res = engine.process_response(q_node, "OMIT", phase_label=f"Guía {AXIS_LABELS[active_axis]}")
                        st.session_state.asked_ids.append(q_node.node_id)
                        st.session_state.unit_workout_answers[ans_key] = {"selected": None, "state": state_res}
                        st.rerun()

                if ans_key in st.session_state.unit_workout_answers:
                    record = st.session_state.unit_workout_answers[ans_key]
                    u_sel, u_state = record["selected"], record["state"]
                    ai_cache_key = f"unit_{ans_key}_{u_sel}_{u_state}"
                    st.divider()
                    if u_state == "CORRECT":
                        st.success(f"🎉 **¡Correcto! Alternativa {u_sel}).**")
                    elif u_state == "OMITTED":
                        st.warning(f"🏳️ **Omitida.** La clave oficial DEMRE es **{q_node.correct_option})**.")
                    else:
                        st.error(f"❌ **Incorrecta.** Marcaste {u_sel}), pero la clave es **{q_node.correct_option})**.")

                    if ai_cache_key not in st.session_state.ai_explanations_cache:
                        with st.spinner("🤖 Generando explicación paso a paso en LaTeX..."):
                            st.session_state.ai_explanations_cache[ai_cache_key] = GoPAESLLMCoach.generate_live_latex_explanation(
                                question=q_node, selected_option=u_sel, state=u_state
                            )
                    st.markdown(st.session_state.ai_explanations_cache[ai_cache_key])


# =====================================================================
# SECCIÓN 4: ENSAYOS PAES (FULL 65, ADAPTATIVO Y MODO GENERAL)
# =====================================================================
elif st.session_state.nav_section == "EXAMS":
    st.title("📝 Motor de Ensayos GoPAES")

    if st.session_state.exam_subphase == "CONFIG":
        col_full, col_custom = st.columns(2)

        with col_full:
            with st.container(border=True):
                st.subheader("🏛️ Ensayo Full Oficial PAES (65 Preguntas)")
                st.write(
                    "Simulación oficial con la proporción exacta de las 4 Unidades del DEMRE:\n"
                    "- **16** de Unidad 1: Números (24,6%)\n"
                    "- **22** de Unidad 2: Álgebra y Funciones (33,8%)\n"
                    "- **14** de Unidad 3: Geometría (21,5%)\n"
                    "- **13** de Unidad 4: Probabilidad y Estadística (20,0%)"
                )
                full_timed = st.radio(
                    "Modalidad de Tiempo:",
                    options=[True, False],
                    format_func=lambda t: "⏱️ Cronometrado Oficial (2h 20m / 140 min)" if t else "🧘 Modo Libre",
                    key="full_65_timer_radio",
                )
                if st.button("🏛️ Iniciar Ensayo Full (65 Preguntas) →", type="primary", use_container_width=True):
                    queue_65 = engine.build_exam_question_queue(
                        vector_store=st.session_state.vector_store,
                        exam="M1",
                        num_questions=65,
                        mode="OFFICIAL_65",
                        asked_ids=st.session_state.asked_ids,
                    )
                    st.session_state.exam_config = {
                        "exam": "M1",
                        "num_questions": 65,
                        "timed_mode": full_timed,
                        "allocated_seconds": 65 * OFFICIAL_SECONDS_PER_QUESTION["M1"],
                        "selection_mode": "OFFICIAL_65",
                        "focus_axis": None,
                    }
                    st.session_state.exam_queue = queue_65
                    st.session_state.exam_history = []
                    st.session_state.exam_subphase = "ACTIVE_RUN"
                    st.rerun()

        with col_custom:
            with st.container(border=True):
                st.subheader("🔥 Ensayo a Medida / Debilidades")
                ignore_weights = st.toggle(
                    "⚖️ Modo Ensayo General (Ignorar temporalmente mis debilidades al elegir preguntas)",
                    value=(st.session_state.exam_config.get("selection_mode") == "GENERAL_STANDARD"),
                )
                chosen_mode: SelectionMode = "GENERAL_STANDARD" if ignore_weights else "ADAPTIVE"

                exam_choice: ExamType = st.radio(
                    "Prueba PAES:",
                    options=["M1", "M2"],
                    horizontal=True,
                    index=0 if st.session_state.exam_config.get("exam", "M1") == "M1" else 1,
                    format_func=lambda x: "M1 (Obligatoria)" if x == "M1" else "M2 (Electiva Científica)",
                )
                unit_filter = st.selectbox(
                    "Unidad a evaluar:",
                    options=["ALL_UNITS"] + list(ALL_AXES),
                    format_func=lambda a: (
                        "🧠 Todas las 4 Unidades (Adaptativo)"
                        if a == "ALL_UNITS"
                        else f"{UNIT_ICONS[a]} Solo {UNIT_NUMBER_LABELS[a]}"
                    ),
                )
                num_q = st.slider(
                    "Cantidad de preguntas:",
                    min_value=2,
                    max_value=65 if exam_choice == "M1" else 55,
                    value=10,
                )
                custom_timed = st.radio(
                    "Tiempo:",
                    options=[True, False],
                    horizontal=True,
                    format_func=lambda t: "⏱️ Sincronizado DEMRE" if t else "🧘 Modo Libre",
                )
                sec_per_q = OFFICIAL_SECONDS_PER_QUESTION[exam_choice]
                if st.button(f"🚀 Iniciar Ensayo {exam_choice} ({num_q} preg.) →", type="primary", use_container_width=True):
                    focus_ax = None if unit_filter == "ALL_UNITS" else unit_filter
                    queue = engine.build_exam_question_queue(
                        vector_store=st.session_state.vector_store,
                        exam=exam_choice,
                        num_questions=num_q,
                        mode=chosen_mode,
                        asked_ids=st.session_state.asked_ids,
                        focus_axis=focus_ax,  # type: ignore
                    )
                    st.session_state.exam_config = {
                        "exam": exam_choice,
                        "num_questions": len(queue),
                        "timed_mode": custom_timed,
                        "allocated_seconds": len(queue) * sec_per_q,
                        "selection_mode": chosen_mode,
                        "focus_axis": focus_ax,
                    }
                    st.session_state.exam_queue = queue
                    st.session_state.exam_history = []
                    st.session_state.exam_subphase = "ACTIVE_RUN"
                    st.rerun()

    elif st.session_state.exam_subphase == "ACTIVE_RUN":
        cfg = st.session_state.exam_config
        step_idx = len(st.session_state.exam_history)
        total_q = len(st.session_state.exam_queue)

        if step_idx >= total_q:
            engine.register_completed_exam()
            st.session_state.exam_subphase = "COACHING_RESULTS"
            st.rerun()

        q: DEMREQuestionNode = st.session_state.exam_queue[step_idx]
        col_reason, col_finish = st.columns([3.5, 1.2])
        with col_reason:
            st.info(
                f"🚀 **Ensayo PAES {cfg['exam']}** • **{UNIT_NUMBER_LABELS[q.thematic_axis]}** ({q.subtopic_name})"
            )
        with col_finish:
            if st.button("🏁 Finalizar Ensayo", type="secondary", use_container_width=True):
                if st.session_state.exam_history:
                    engine.register_completed_exam()
                st.session_state.exam_subphase = "COACHING_RESULTS"
                st.rerun()

        with st.container(border=True):
            render_question_card(
                question=q,
                step_num=step_idx + 1,
                total_steps=total_q,
                badge_text=f"🚀 GoPAES {cfg['exam']}",
            )
            st.divider()
            user_choice = st.radio(
                "Selecciona una alternativa:",
                options=[o.key for o in q.options],
                format_func=lambda k: f"Alternativa {k}",
                horizontal=True,
                key=f"exam_radio_{step_idx}_{q.node_id}",
            )
            col_ans, col_blank = st.columns(2)

            def record_and_advance(chosen_opt):
                state = engine.process_response(q, chosen_opt, phase_label="Ensayo GoPAES")
                st.session_state.asked_ids.append(q.node_id)
                st.session_state.exam_history.append({
                    "question": q,
                    "selected_option": chosen_opt,
                    "state": state,
                })
                if len(st.session_state.exam_history) >= total_q:
                    engine.register_completed_exam()
                    st.session_state.exam_subphase = "COACHING_RESULTS"
                st.rerun()

            with col_ans:
                if st.button("✅ Responder y Avanzar →", type="primary", use_container_width=True):
                    record_and_advance(user_choice)
            with col_blank:
                if st.button("🏳️ Dejar en blanco", type="secondary", use_container_width=True):
                    record_and_advance(None)

    elif st.session_state.exam_subphase == "COACHING_RESULTS":
        st.balloons()
        st.subheader("🎓 GoPAES Coaching IA • Análisis Paso a Paso en LaTeX")
        history = st.session_state.exam_history
        correct_total = sum(1 for h in history if h["state"] == "CORRECT")
        incorrect_total = sum(1 for h in history if h["state"] == "INCORRECT")
        omitted_total = sum(1 for h in history if h["state"] == "OMITTED")
        attempted_total = correct_total + incorrect_total
        net_acc = round((correct_total / attempted_total) * 100, 1) if attempted_total > 0 else 0.0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("✅ Correctas", correct_total)
        m2.metric("❌ Errores", incorrect_total)
        m3.metric("🏳️ Omitidas", omitted_total)
        m4.metric("🎯 Precisión Neta", f"{net_acc}%")

        for idx, item in enumerate(history):
            q: DEMREQuestionNode = item["question"]
            sel = item["selected_option"]
            st_resp = item["state"]
            cache_key = f"{idx}_{q.node_id}_{sel}_{st_resp}"

            with st.container(border=True):
                if st_resp == "CORRECT":
                    st.success(f"**Pregunta {idx + 1} ({UNIT_NUMBER_LABELS[q.thematic_axis]}): ✅ CORRECTA ({sel})**")
                elif st_resp == "OMITTED":
                    st.warning(f"**Pregunta {idx + 1} ({UNIT_NUMBER_LABELS[q.thematic_axis]}): 🏳️ OMITIDA (Clave: {q.correct_option})**")
                else:
                    st.error(f"**Pregunta {idx + 1} ({UNIT_NUMBER_LABELS[q.thematic_axis]}): ❌ ERROR (Marcaste {sel} • Clave: {q.correct_option})**")

                st.write(q.stem_text)
                st.latex(q.stem_latex)

                if cache_key not in st.session_state.ai_explanations_cache:
                    with st.spinner(f"🤖 Generando explicación matemática para la Pregunta {idx + 1}..."):
                        st.session_state.ai_explanations_cache[cache_key] = GoPAESLLMCoach.generate_live_latex_explanation(
                            question=q, selected_option=sel, state=st_resp
                        )
                st.markdown(st.session_state.ai_explanations_cache[cache_key])

        if st.button("🏠 Volver al Inicio", type="primary"):
            st.session_state.exam_subphase = "CONFIG"
            st.session_state.nav_section = "DASHBOARD"
            st.rerun()

# Pie de página institucional GoPAES (como en la imagen de referencia)
st.markdown(
    """
    <div style="text-align:center; color:#94A3B8; font-size:0.82rem; margin-top:42px; padding:18px 0; border-top:1px solid #E2E8F0;">
        GoPAES - Plataforma Integral de Preparación PAES Matemática (M1 y M2) • Preguntas pedagógicas y currículum oficial DEMRE.
    </div>
    """,
    unsafe_allow_html=True,
)
