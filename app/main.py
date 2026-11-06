from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import auth, models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Todo API", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(body: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(models.User).where(models.User.email == body.email)):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(email=body.email, hashed_password=auth.hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == form.username))
    if not user or not auth.verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong email or password")
    return schemas.Token(access_token=auth.create_access_token(user.id))


@app.get("/tasks", response_model=list[schemas.TaskOut])
def list_tasks(
    done: bool | None = None,
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.current_user),
):
    q = select(models.Task).where(models.Task.owner_id == user.id)
    if done is not None:
        q = q.where(models.Task.done == done)
    return db.scalars(q.order_by(models.Task.created_at.desc()).limit(limit).offset(offset)).all()


@app.post("/tasks", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    body: schemas.TaskCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.current_user),
):
    task = models.Task(title=body.title, owner_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def _own_task(task_id: int, db: Session, user: models.User) -> models.Task:
    task = db.get(models.Task, task_id)
    if not task or task.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: int,
    body: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.current_user),
):
    task = _own_task(task_id, db, user)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), user: models.User = Depends(auth.current_user)):
    db.delete(_own_task(task_id, db, user))
    db.commit()
