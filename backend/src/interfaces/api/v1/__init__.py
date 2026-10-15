from fastapi import APIRouter

from ....infrastructure.auth.routes import router as auth_router
from ....modules.api_keys.routes import router as api_keys_router
from ....modules.config_experimento.routes import router as config_experimento_router
from ....modules.geracao.routes import router as geracao_router
from ....modules.matriz_referencia.routes import router as matriz_referencia_router
from ....modules.obsidian.routes import router as obsidian_router
from ....modules.questoes.routes import router as questoes_router
from ....modules.rate_limit.routes import router as rate_limits_router
from ....modules.tier.routes import router as tiers_router
from ....modules.user.routes import router as users_router
from ....modules.validacao.routes import router as validacao_router

router = APIRouter(prefix="/v1")
router.include_router(users_router, prefix="/users")
router.include_router(tiers_router, prefix="/tiers")
router.include_router(rate_limits_router, prefix="/rate-limits")
router.include_router(auth_router, prefix="/auth")
router.include_router(api_keys_router, prefix="/api-keys")
router.include_router(matriz_referencia_router, prefix="/matriz")
router.include_router(validacao_router, prefix="/validacao")
router.include_router(geracao_router, prefix="/geracao")
router.include_router(config_experimento_router, prefix="/config")
router.include_router(questoes_router, prefix="/questoes")
router.include_router(obsidian_router, prefix="/obsidian")
