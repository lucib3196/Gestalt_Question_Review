# --- Standard Library ---
from typing import List, Literal, Optional, Union, Annotated
from uuid import UUID
from fastapi import UploadFile

# --- Third-Party ---
from fastapi import APIRouter, HTTPException
from starlette import status

# --- Internal ---
from src.api.database import SessionDep
from src.api.models.models import Question, QuestionMeta
from src.api.response_models import *
from src.api.service.crud import question_crud
from src.api.service import refactor_question_storage_service as qs
from src.utils import normalize_kwargs
from src.api.service import file_management as fm
from fastapi import FastAPI, File, UploadFile
from typing import Dict
from fastapi import Form
import json
from src.api.models.models import Language

router = APIRouter(prefix="/file_uploads", tags=["file_uploads"])


class UploadQuesiton(BaseModel):
    question: Union[Question, dict]
    additional_metadata: Optional[AdditionalQMeta] = None

# TODO Can delete this soon 
def parse_payload(qdata: str | dict | Question, additional_metadata: Optional[str]):
    base_question: Dict[str, Any] | None = None
    qdata = json.loads(str(qdata))
    if not qdata:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question data is empty,data:  {qdata}",
        )
    if isinstance(qdata, Question):
        base_question = qdata.model_dump()
    elif isinstance(qdata, dict):
        base_question = qdata
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"expected dict or type Question received type {type(qdata)}",
        )
    metadata = None
    if additional_metadata:
        metadata = AdditionalQMeta.model_validate(json.loads(additional_metadata))
        base_question = {**base_question, **metadata.model_dump()}
    return base_question, metadata


BaseFiles = {
    "question.html": {
        "boiler_plate": """<pl-question-panel>
  <h2>Sample Question</h2>
  <p>Replace this with your question text.</p>
</pl-question-panel>
"""
    },
    "solution.html": {
        "boiler_plate": """<pl-question-panel>
  <h2>Solution</h2>
  <p>Replace this with your solution text.</p>
  <pl-hint>
    <p>This is a hint to guide the student.</p>
  </pl-hint>
</pl-question-panel>
"""
    },
}



BaseServerFiles = {
    "server.js": """function generate() {
  console.log("Hello World")
  return {};
}

module.exports = { generate };
""",
    "server.py": """def generate():
    print("Hello World")

if __name__ == "__main__":
    generate()
""",
}


def create_base_files(languages: list[Language], is_adaptive: bool):
    try:
        n_languages = [l.name for l in languages]
        files_data: List[FileData] = []
        # Create some base files
        question_html = FileData(
            filename="question.html",
            content=BaseFiles["question.html"]["boiler_plate"],
        )
        solution_html = FileData(
            filename="solution.html",
            content=BaseFiles["solution.html"]["boiler_plate"],
        )
        files_data.append(question_html)
        files_data.append(solution_html)

        if is_adaptive:
            if "javascript" in n_languages:
                server_js = FileData(
                    filename="server.js",
                    content=BaseServerFiles["server.js"],
                )
                files_data.append(server_js)

            if "python" in n_languages:
                server_py = FileData(
                    filename="server.py",
                    content=BaseServerFiles["server.py"],
                )
                files_data.append(server_py)
        return files_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/create_question/upload")
async def create_question_file_upload(
    session: SessionDep,
    question: str = Form(...),  # incoming as string
    additional_metadata: Optional[str] = Form(None),
    files: Optional[list[UploadFile]] = File(None),
    save_dir: Literal["local", "firebase"] = "local",
):
    try:
        base_question, metadata = parse_payload(question, additional_metadata)
        if metadata:
            base_question = {**base_question, **metadata.model_dump()}
        q, qdata = await qs.create_question_full(base_question, session)

        if save_dir == "local":
            response = await qs.set_directory(q.id, session)
        elif save_dir == "firebase":
            raise NotImplementedError("Have not implemented firebase functionality")

        file_data_list = []  # Storing of the files that will be created
        # Inspect the filedata
        if not files:
            file_data_list = create_base_files(
                languages=q.languages, is_adaptive=q.isAdaptive
            )
        else:
            for f in files:
                f = await fm.validate_file(f)
                content = await f.read()
                await f.seek(0)
                fd = FileData(filename=str(f.filename), content=content)
                file_data_list.append(fd)
        await qs.write_files_to_directory(
            question_id=q.id, files_data=file_data_list, session=session
        )
        return {"detail": "okay", "question": q, "metadata": metadata}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{qid}/upload_file/")
# async def upload_files_to_question(
#     qid: str | UUID,
#     session: SessionDep,
#     files: list[UploadFile] = File(...),
#     save_dir: Literal["local", "firebase"] = "local",
# ):
#     try:
#         # Validate files
#         file_data_list = []
#         for f in files:
#             # Validate UploadFile (assuming fm.validate_file returns UploadFile)
#             f = await fm.validate_file(f)
#             content = await f.read()
#             await f.seek(0)

#             # Wrap in FileData
#             fd = FileData(filename=str(f.filename), content=content)

#             file_data_list.append(fd)
#         response = await qs.write_files_to_directory(qid, file_data_list, session)
#         return {"detail": "okay", "files": response.files}
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
