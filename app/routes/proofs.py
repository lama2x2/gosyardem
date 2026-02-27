"""Пруфы: загрузка исполнителем, подтверждение/отклонение оператором."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Proof, CitizenRequest
from app.models.proof import ProofStatus as ModelProofStatus
from app.schemas.proof import ProofCreate, ProofRead, ProofDecide, ProofStatus

router = APIRouter()


@router.get("/", response_model=List[ProofRead])
async def list_proofs(request_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Список пруфов, опционально по request_id."""
    q = select(Proof)
    if request_id is not None:
        q = q.where(Proof.request_id == request_id)
    q = q.order_by(Proof.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("/", response_model=ProofRead)
async def create_proof(
    body: ProofCreate,
    db: AsyncSession = Depends(get_db),
):
    """Исполнитель прикладывает пруф к заявке. executor_id в теле запроса."""
    req = await db.get(CitizenRequest, body.request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    proof = Proof(
        request_id=body.request_id,
        executor_id=body.executor_id,
        file_ref=body.file_ref,
        comment=body.comment,
        status=ModelProofStatus.pending,
    )
    db.add(proof)
    await db.flush()
    await db.refresh(proof)
    return proof


@router.get("/{proof_id}", response_model=ProofRead)
async def get_proof(proof_id: int, db: AsyncSession = Depends(get_db)):
    proof = await db.get(Proof, proof_id)
    if not proof:
        raise HTTPException(404, "Proof not found")
    return proof


@router.patch("/{proof_id}/decide", response_model=ProofRead)
async def decide_proof(
    proof_id: int,
    body: ProofDecide,
    db: AsyncSession = Depends(get_db),
):
    """Оператор подтверждает или отклоняет пруф."""
    proof = await db.get(Proof, proof_id)
    if not proof:
        raise HTTPException(404, "Proof not found")
    if proof.status != ModelProofStatus.pending:
        raise HTTPException(400, "Proof already decided")
    proof.status = ModelProofStatus(body.status.value)
    proof.operator_id = body.operator_id
    await db.flush()
    await db.refresh(proof)
    return proof
