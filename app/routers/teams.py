from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from ..core.database import get_db as get_session
from ..models.db_models import Team, QuestionPaper, User
from ..auth.dependencies import get_super_admin_user, get_admin_user
from ..schemas.requests import TeamCreate, TeamUpdate
from ..schemas.responses import TeamRead, TeamReadBasic, PaperRead, QuestionRead
from ..schemas.api_response import ApiResponse
from ..core.logger import get_logger
from ..utils import format_iso_datetime

logger = get_logger(__name__)

router = APIRouter(prefix="/super-admin", tags=["Teams"])

def _serialize_team(team: Team, session: Session) -> TeamRead:
    """Convert a Team ORM object to a TeamRead schema with nested users."""
    # Load all users for this team
    users_orm = session.exec(
        select(User).where(User.team_id == team.id)
    ).all()

    users_out = []
    for u in users_orm:
        # Get team basic for UserRead
        team_basic = TeamReadBasic(
            id=team.id,
            name=team.name,
            description=team.description,
            created_at=team.created_at.isoformat() if team.created_at else "",
            user_count=len(users_orm)
        )
        users_out.append(UserRead(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.value if hasattr(u.role, "value") else str(u.role),
            team=team_basic
        ))

    return TeamRead(
        id=team.id,
        name=team.name,
        description=team.description,
        created_at=team.created_at.isoformat() if team.created_at else "",
        user_count=len(users_out),
        users=users_out,
    )

def _serialize_team_basic(team: Team, session: Session) -> TeamReadBasic:
    from sqlalchemy import func
    user_count = session.exec(
        select(func.count(User.id)).where(User.team_id == team.id)
    ).one()

    return TeamReadBasic(
        id=team.id,
        name=team.name,
        description=team.description,
        created_at=team.created_at.isoformat() if team.created_at else "",
        user_count=user_count,
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
        description=team_data.description
    )
    session.add(new_team)
    try:
        session.commit()
        session.refresh(new_team)
        pass
    except IntegrityError as e:
        session.rollback()
        logger.error(f"IntegrityError creating team: {str(e)}")
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

@router.get("/teams", response_model=ApiResponse[List[TeamReadBasic]])
async def list_teams(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """
    List all teams. Returns only basic team information without nested papers.
    *(Admin + Super Admin)*
    """
    teams = session.exec(select(Team).order_by(Team.name)).all()
    for t in teams:
        pass
            
    # Serialize, completely omitting nested data
    data = []
    for t in teams:
        data.append(_serialize_team_basic(t, session))
        
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
        pass
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
    Delete a team. Users in this team will have their team_id set to NULL.
    *(Super Admin only)*
    """
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # BUSINESS RULE: Prevent deleting teams with assigned users
    user_exists = session.exec(
        select(User).where(User.team_id == team_id).limit(1)
    ).first()
    
    if user_exists:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete team. Users are still assigned to this team. Please reassign or remove those users first."
        )

    try:
        # Note: QuestionPapers no longer have team_id, so we don't handle them here.
        # If the team is empty, no users belong to it, thus no 'team papers' exist.
        session.delete(team)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error during team deletion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete team: {str(e)}")

    return ApiResponse(
        status_code=200,
        data={},
        message=f"Team '{team.name}' deleted successfully"
    )
