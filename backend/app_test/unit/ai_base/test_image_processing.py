# # --- Standard Library ---
# from pathlib import Path
# import json

# # --- Third-Party ---
# import pytest
# from langchain.chat_models import init_chat_model

# # --- Internal Imports ---
# from src.ai_base.image_processing import (
#     langchain_multimodal,
#     openai_multimodal,
#     BaseOutput,
# )
# from src.utils import encode_image



# @pytest.fixture
# def image_payload():
#     # Relative to backend folder where i should be runnign this
#     test_image = Path(r"src/app_test/test_assets/images/test_image.png").resolve()
#     assert test_image.exists()
#     return encode_image(test_image.as_posix())


# @pytest.fixture
# def base_prompt():
#     return "What is in the image"


# @pytest.fixture
# def test_llm():
#     return init_chat_model(model="gpt-4o", model_provider="openai")


# def test_langchain(base_prompt, image_payload, test_llm):
#     resp = langchain_multimodal(base_prompt, image_payload, test_llm)
#     assert resp
#     parsed = BaseOutput.model_validate(resp)
#     assert parsed
#     assert parsed.data != None


# def test_openai(base_prompt, image_payload, test_llm):
#     resp = openai_multimodal(
#         base_prompt,
#         image_payload,
#     )
#     assert resp
#     print(resp, type(resp))
#     parsed = BaseOutput.model_validate(json.loads(resp))

#     assert parsed
#     assert parsed.data != None
