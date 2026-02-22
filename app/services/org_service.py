# app/services/org_service.py
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.hierarchy_repo import HierarchyRepository

class OrgService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = HierarchyRepository(db)

    def get_approver_for_user(self, submitter_id: UUID, required_role: str) -> UUID:
        """
        Dynamically resolves 'Who should approve this?'
        Traverses UP the user's specific reporting chain to find the nearest ancestor
        holding the `required_role` (e.g., 'MANAGER' or 'HOD').
        """
        # 1. Find where the submitter sits in the org tree
        user_positions = self.repo.get_user_positions(submitter_id)
        if not user_positions:
            raise HTTPException(status_code=400, detail="Submitter has no assigned position.")
        
        # We assume a primary position for simplicity here
        starting_position_id = user_positions[0].id

        # 2. Get the entire chain up to the CEO (Using the Recursive CTE)
        # The repo returns the chain ordered from bottom (submitter) to top
        ancestor_positions = self.repo.get_ancestor_positions(starting_position_id)

        # 3. Find the nearest ancestor matching the required role
        for pos in ancestor_positions:
            if pos.role_type == required_role:
                # We found the correct position! Now, who holds this position?
                users_in_position = self.repo.get_users_by_position(pos.id)
                if not users_in_position:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Position '{pos.title}' requires approval, but no active user is assigned to it."
                    )
                # Return the ID of the manager/HOD
                return users_in_position[0].id

        # If we reach the top of the tree without finding the role
        raise HTTPException(
            status_code=404, 
            detail=f"No ancestor with role '{required_role}' found in the submitter's reporting chain."
        )