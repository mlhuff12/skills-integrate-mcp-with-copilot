"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        _seed_data_if_needed(db)
    yield


app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
    lifespan=lifespan,
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# SQLite persistence
default_db_path = current_dir / "school.db"
database_url = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=False)
    schedule = Column(String, nullable=False)
    max_participants = Column(Integer, nullable=False)
    participants = relationship(
        "ActivityParticipant",
        back_populates="activity",
        cascade="all, delete-orphan",
    )


class ActivityParticipant(Base):
    __tablename__ = "activity_participants"
    __table_args__ = (UniqueConstraint("activity_id", "email", name="uq_activity_email"),)

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    email = Column(String, nullable=False)
    activity = relationship("Activity", back_populates="participants")


SEED_ACTIVITIES = [
    {
        "name": "Chess Club",
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    {
        "name": "Programming Class",
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    {
        "name": "Gym Class",
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    {
        "name": "Soccer Team",
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    {
        "name": "Basketball Team",
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    {
        "name": "Art Club",
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    {
        "name": "Drama Club",
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    {
        "name": "Math Club",
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    {
        "name": "Debate Team",
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _seed_data_if_needed(db: Session):
    if db.query(Activity).count() > 0:
        return

    for item in SEED_ACTIVITIES:
        activity = Activity(
            name=item["name"],
            description=item["description"],
            schedule=item["schedule"],
            max_participants=item["max_participants"],
        )
        db.add(activity)
        db.flush()

        for email in item["participants"]:
            db.add(ActivityParticipant(activity_id=activity.id, email=email))

    db.commit()


def _activity_to_response(activity: Activity):
    participants = [participant.email for participant in activity.participants]
    return {
        "description": activity.description,
        "schedule": activity.schedule,
        "max_participants": activity.max_participants,
        "participants": participants,
    }


def _normalize_email_or_400(email: str) -> str:
    normalized_email = email.strip().lower()
    if not normalized_email:
        raise HTTPException(status_code=400, detail="Email is required")
    return normalized_email


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities(db: Session = Depends(get_db)):
    records = db.query(Activity).order_by(Activity.name).all()
    return {activity.name: _activity_to_response(activity) for activity in records}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, db: Session = Depends(get_db)):
    """Sign up a student for an activity"""
    email = _normalize_email_or_400(email)

    activity = db.query(Activity).filter(Activity.name == activity_name).first()
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    existing_signup = (
        db.query(ActivityParticipant)
        .filter(ActivityParticipant.activity_id == activity.id, ActivityParticipant.email == email)
        .first()
    )
    if existing_signup is not None:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    current_count = db.query(ActivityParticipant).filter(
        ActivityParticipant.activity_id == activity.id
    ).count()
    if current_count >= activity.max_participants:
        raise HTTPException(status_code=400, detail="Activity is full")

    db.add(ActivityParticipant(activity_id=activity.id, email=email))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Student is already signed up")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to complete signup at this time")

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, db: Session = Depends(get_db)):
    """Unregister a student from an activity"""
    email = _normalize_email_or_400(email)

    activity = db.query(Activity).filter(Activity.name == activity_name).first()
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    signup = (
        db.query(ActivityParticipant)
        .filter(ActivityParticipant.activity_id == activity.id, ActivityParticipant.email == email)
        .first()
    )
    if signup is None:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    db.delete(signup)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to complete unregister at this time")

    return {"message": f"Unregistered {email} from {activity_name}"}
