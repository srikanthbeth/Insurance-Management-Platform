from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, require_roles
from schemas.customer import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdate,
)
from services.customer_service import (
    create_customer_service,
    delete_customer_service,
    get_customer_service,
    get_customers_service,
    update_customer_service,
)

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_roles(
                "Super Admin",
                "Insurance Agent",
                
            )
        )
    ],
)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
):
    return create_customer_service(
        db,
        data,
    )


@router.get(
    "",
    response_model=CustomerListResponse,
    dependencies=[
        Depends(
            require_roles(
                "Super Admin",
                "Insurance Agent",
                "Claims Officer",
                "Finance Officer",
            )
        )
    ],
)
def get_customers(
    db: Session = Depends(get_db),
):
    customers = get_customers_service(db)

    return {
        "success": True,
        "data": customers,
    }


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    dependencies=[
        Depends(get_current_user),
    ],
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    return get_customer_service(
        db,
        customer_id,
    )


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
    dependencies=[
        Depends(
            require_roles(
                "Super Admin",
                "Insurance Agent",
            )
        )
    ],
)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
):
    return update_customer_service(
        db,
        customer_id,
        data,
    )

@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            require_roles(
                "Super Admin",
            )
        )
    ],
)
def delete_customer(
    customer_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_customer_service(
        db,
        customer_id,
        current_user,
    )