# app/repositories/hierarchy_repo.py
from uuid import UUID
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select

from app.models.organization import Position, UserPosition, User

class HierarchyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_positions(self, user_id: UUID) -> list[Position]:
        """Fetches all positions a user currently holds."""
        return self.db.query(Position).join(UserPosition).filter(
            UserPosition.user_id == user_id
        ).all()

    def get_ancestor_positions(self, starting_position_id: UUID):
        """
        THE INFINITE HIERARCHY RESOLVER.
        Uses a Recursive CTE to traverse UP the organization chart.
        Returns a list of all parent positions in order from bottom to top.
        """
        # 1. Base Case: The starting position
        base_query = (
            select(Position)
            .where(Position.id == starting_position_id)
            .cte(name="position_hierarchy", recursive=True)
        )

        # 2. Recursive Case: Join the Position table to the CTE going UP the tree
        PositionAlias = aliased(Position)
        recursive_query = (
            select(PositionAlias)
            .join(base_query, PositionAlias.id == base_query.c.parent_position_id)
        )

        # 3. Combine them
        hierarchy_cte = base_query.union_all(recursive_query)

        # 4. Execute the query
        statement = select(hierarchy_cte)
        result = self.db.execute(statement).all()
        
        # Returns a list of Row objects representing the positions
        return result

    def get_users_by_position(self, position_id: UUID) -> list[User]:
        """Finds which actual humans occupy a specific position (e.g., Who is the HOD?)."""
        return self.db.query(User).join(UserPosition).filter(
            UserPosition.position_id == position_id,
            User.is_active == True
        ).all()