from fastapi import APIRouter, HTTPException, Depends, Path
from src.domain.entities.school import School
from src.application.school.get_school_by_id.get_school_by_id import (
    GetSchoolById,
)
from .callable.school_callable import get_school_by_id_use_case
from src.application.school.get_school_by_id.get_school_by_id_dto import (
    GetSchoolByIdDTO,
)


class GetSchoolByIdController:
    def __init__(self, get_school_by_id_use_case: GetSchoolById):
        self.get_school_by_id_use_case = get_school_by_id_use_case

    async def handle(self, escola_id_inep: str) -> School:
        dto = GetSchoolByIdDTO(escola_id_inep=escola_id_inep)

        result = await self.get_school_by_id_use_case.execute(dto=dto)

        if not result:
            raise HTTPException(status_code=404, detail="School not found")

        return result


router = APIRouter()


@router.get("/{escola_id_inep}", response_model=School)
async def get_school_by_id(
    escola_id_inep: str = Path(..., description="Identificador INEP da escola"),
    get_school_by_id_use_case: GetSchoolById = Depends(
        get_school_by_id_use_case
    ),
):
    controller = GetSchoolByIdController(get_school_by_id_use_case)

    result = await controller.handle(escola_id_inep=escola_id_inep)

    return result