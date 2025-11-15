from .questions.init import routes as questions_routes
from .ai_generation.code_generator import router as code_generation_router
from .startup import router as general_router
from .run_question_server import router as question_runner
from .generic import routes as generic_routes
from .user import router as user_route

routes = [code_generation_router, general_router, question_runner, user_route]

routes.extend(questions_routes)
routes.extend(generic_routes)
