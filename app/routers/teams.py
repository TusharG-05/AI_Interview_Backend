from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from ..core.database import get_db as get_session
from ..models.db_models import Team, QuestionPaper, User
from ..auth.dependencies import get_super_admin_user, get_admin_user
from ..schemas.requests import TeamCreate, TeamUpdate
from ..schemas.responses import TeamRead, PaperRead, QuestionRead
from ..schemas.api_response import ApiResponse
from ..core.logger import get_logger
from ..utils import format_iso_datetime

logger = get_logger(__name__)

router = APIRouter(prefix="/super-admin", tags=["Teams"])

def _serialize_team(team: Team, session: Session) -> TeamRead:
    """Convert a Team ORM object to a TeamRead schema with full nested papers and questions."""
    from ..schemas.user_schemas import serialize_user_flat

    creator_dict = serialize_user_flat(team.creator) if team.creator else None

    # Load all papers for this team, with their questions and creator info
    papers_orm = session.exec(
        select(QuestionPaper).where(QuestionPaper.team_id == team.id)
    ).all()

    papers_out = []
    for paper in papers_orm:
        # Get question objects (lazy-loaded or manually fetched)
        from ..models.db_models import Questions
        questions_orm = session.exec(
            select(Questions).where(Questions.paper_id == paper.id)
        ).all()

        questions_out = [
            QuestionRead(
                id=q.id,
                content=q.content or "",
                question_text=q.question_text or "",
                topic=q.topic or "",
                difficulty=q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty),
                marks=q.marks or 1,
                response_type=q.response_type.value if hasattr(q.response_type, "value") else str(q.response_type),
            )
            for q in questions_orm
        ]

        # Paper creator info
        paper_creator = None
        if paper.adminUser:
            admin_user = session.get(User, paper.adminUser)
            if admin_user:
                paper_creator = serialize_user_flat(admin_user)

        papers_out.append(PaperRead(
            id=paper.id,
            name=paper.name,
            description=paper.description,
            created_by=paper_creator,
            created_at=paper.created_at.isoformat() if paper.created_at else "",
            question_count=len(questions_out),
            total_marks=paper.total_marks or 0,
            questions=questions_out,
        ))

    return TeamRead(
        id=team.id,
        name=team.name,
        description=team.description,
        created_by=creator_dict,
        created_at=team.created_at.isoformat(),
        paper_count=len(papers_out),
        papers=papers_out,
    )


# ---------------------------------------------------------------------------
# CREATE — Super Admin only
# ---------------------------------------------------------------------------

@router.post("/teams", response_model=ApiResponse[TeamRead], status_code=201)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_super_admin_user),
    session: Session = Depends(get_session)
):
    """
    Create a new team.  
    Team names are **globally unique** — a 409 is returned if the name already exists.  
    *(Super Admin only)*
    """
    # Strip and normalise
    name = team_data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Team name cannot be empty")

    new_team = Team(
        name=name,
        description=team_data.description,
        created_by=current_user.id
    )
    session.add(new_team)
    try:
        session.commit()
        session.refresh(new_team)
        # Eager-load creator for serialisation
        if new_team.created_by:
            new_team.creator = session.get(User, new_team.created_by)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A team with the name '{name}' already exists. Team names must be globally unique."
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")

    return ApiResponse(
        status_code=201,
        data=_serialize_team(new_team, session),
        message="Team created successfully"
    )


# ---------------------------------------------------------------------------
# LIST — Admin + Super Admin
# ---------------------------------------------------------------------------

@router.get("/teams", response_model=ApiResponse[List[TeamRead]])
async def list_teams(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """
    List all teams.  
    *(Admin + Super Admin)*
    """
    teams = session.exec(select(Team).order_by(Team.name)).all()
    # Eager-load creators
    for t in teams:
        if t.created_by:
            t.creator = session.get(User, t.created_by)
    data = [_serialize_team(t, session) for t in teams]
    return ApiResponse(
        status_code=200,
        data=data,
        message="Teams retrieved successfully"
    )


# ---------------------------------------------------------------------------
# GET ONE — Admin + Super Admin
# ---------------------------------------------------------------------------

@router.get("/teams/{team_id}", response_model=ApiResponse[TeamRead])
async def get_team(
    team_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """
    Get details of a specific team, including its question paper count.  
    *(Admin + Super Admin)*
    """
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.created_by:
        team.creator = session.get(User, team.created_by)
    return ApiResponse(
        status_code=200,
        data=_serialize_team(team, session),
        message="Team retrieved successfully"
    )


# ---------------------------------------------------------------------------
# UPDATE — Super Admin only
# ---------------------------------------------------------------------------

@router.patch("/teams/{team_id}", response_model=ApiResponse[TeamRead])
async def update_team(
    team_id: int,
    team_update: TeamUpdate,
    current_user: User = Depends(get_super_admin_user),
    session: Session = Depends(get_session)
):
    """
    Update a team's name or description.  
    Returns 409 if the new name conflicts with another existing team.  
    *(Super Admin only)*
    """
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    update_data = team_update.model_dump(exclude_unset=True)
    if "name" in update_data:
        update_data["name"] = update_data["name"].strip()
        if not update_data["name"]:
            raise HTTPException(status_code=400, detail="Team name cannot be empty")

    for key, value in update_data.items():
        setattr(team, key, value)

    session.add(team)
    try:
        session.commit()
        session.refresh(team)
        if team.created_by:
            team.creator = session.get(User, team.created_by)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A team with the name '{update_data.get('name', '')}' already exists."
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update team: {str(e)}")

    return ApiResponse(
        status_code=200,
        data=_serialize_team(team, session),
        message="Team updated successfully"
    )


# ---------------------------------------------------------------------------
# DELETE — Super Admin only
# ---------------------------------------------------------------------------

@router.delete("/teams/{team_id}", response_model=ApiResponse[dict])
async def delete_team(
    team_id: int,
    current_user: User = Depends(get_super_admin_user),
    session: Session = Depends(get_session)
):
    """
    Delete a team.  
    Returns 400 if any question papers are still attached to this team.  
    *(Super Admin only)*
    """
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Guard: cannot delete if papers are attached
    attached_papers = session.exec(
        select(QuestionPaper).where(QuestionPaper.team_id == team_id)
    ).first()
    if attached_papers:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete team because it has question papers associated with it. "
                   "Re-assign or delete those papers first."
        )

    session.delete(team)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete team: {str(e)}")

    return ApiResponse(
        status_code=200,
        data={},
        message=f"Team '{team.name}' deleted successfully"
    )
