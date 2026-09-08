from .start import router as start_router
from .reminders import router as reminders_router
from .sos import router as sos_router
from .memory import router as memory_router
from .music import router as music_router
from .drawing import router as drawing_router
from .reading import router as reading_router
from .animal_quiz import router as animal_quiz_router
from .keksa_extra import router as keksa_extra_router
from .kvest import router as kvest_router
from .ertak import router as ertak_router
from .quiz import router as quiz_router
from .voice import router as voice_router
from .admin import router as admin_router
from .chat import router as chat_router

all_routers = [
    start_router,
    reminders_router,
    sos_router,
    memory_router,
    music_router,
    drawing_router,
    reading_router,
    animal_quiz_router,
    keksa_extra_router,
    kvest_router,
    ertak_router,
    quiz_router,
    voice_router,
    admin_router,
    chat_router
]


