"""Indexed document listing and upload endpoints."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.config import Config
from src.dependencies import get_config, get_rag_service
from src.document_loader import EXTRACTABLE_EXTENSIONS, SUPPORTED_EXTENSIONS
from src.models import (
    DeleteDocumentResponse,
    DocumentModel,
    DocumentsResponse,
    UploadDocumentsResponse,
    UploadedDocumentModel,
)
from src.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])

MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB per file


@router.get(
    "/documents",
    response_model=DocumentsResponse,
    summary="List indexed documents",
    description="Returns every document currently represented in the vector index, with page and chunk counts.",
)
async def list_documents(service: RAGService = Depends(get_rag_service)) -> DocumentsResponse:
    docs = service.list_documents()
    return DocumentsResponse(
        documents=[DocumentModel(filename=d.filename, pages=d.page_count, chunks=d.chunk_count) for d in docs]
    )


@router.post(
    "/documents",
    response_model=UploadDocumentsResponse,
    summary="Upload documents",
    description=(
        "Saves one or more files into the documents directory. Accepts PDF, DOC, DOCX, "
        "and TXT files. This only stores the files on disk — call POST /index afterwards "
        "to include them in the searchable index."
    ),
    responses={400: {"description": "A file was rejected (unsupported type, empty, or too large)"}},
)
async def upload_documents(
    files: List[UploadFile] = File(...),
    config: Config = Depends(get_config),
) -> UploadDocumentsResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided.")

    allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
    max_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)

    # Validate every file up front so a bad file later in the batch can't
    # leave earlier files written to disk while the request as a whole fails.
    contents: List[tuple[str, bytes]] = []
    for upload in files:
        filename = Path(upload.filename or "").name
        suffix = Path(filename).suffix.lower()

        if not filename or suffix not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: '{upload.filename}'. Allowed types: {allowed}",
            )

        content = await upload.read()
        if not content:
            raise HTTPException(status_code=400, detail=f"'{filename}' is empty.")
        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"'{filename}' exceeds the {max_mb}MB upload limit.",
            )

        contents.append((filename, content))

    uploaded: List[UploadedDocumentModel] = []
    for filename, content in contents:
        destination = config.documents_dir / filename
        destination.write_bytes(content)
        logger.info("Saved uploaded document to %s", destination)

        uploaded.append(
            UploadedDocumentModel(
                filename=filename,
                size_bytes=len(content),
                extractable=Path(filename).suffix.lower() in EXTRACTABLE_EXTENSIONS,
            )
        )

    return UploadDocumentsResponse(uploaded=uploaded)


@router.delete(
    "/documents/{filename}",
    response_model=DeleteDocumentResponse,
    summary="Delete a document",
    description=(
        "Removes a document's vectors from the index (updating it in place, no reindex "
        "needed) and deletes its source file from the documents directory."
    ),
    responses={404: {"description": "No document with that filename was found"}},
)
async def delete_document(filename: str, service: RAGService = Depends(get_rag_service)) -> DeleteDocumentResponse:
    safe_filename = Path(filename).name
    if not safe_filename or safe_filename in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    deleted = service.delete_document(safe_filename)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No document named '{safe_filename}' was found.")
    return DeleteDocumentResponse(deleted=True, filename=safe_filename)
