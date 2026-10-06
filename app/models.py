"""SQLAlchemy models.

Content tables (Exam, Unit, Topic, Subtopic, Element, Note, Question, Card, Equation) are re-seeded from
content/ on every start using stable string ids, so content edits never touch progress tables
(Progress, StudentNote, Highlight, InkDocument, Attempt, AttemptAnswer, CardReview, StudyPlan, PlanItem).
"""
from __future__ import annotations

from app.util import utcnow

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


# ---------------------------------------------------------------- syllabus content
class Exam(Base):
    __tablename__ = "exams"
    code: Mapped[str] = mapped_column(String(8), primary_key=True)  # RPLA / PPLA
    name: Mapped[str] = mapped_column(String(120))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    pass_mark_percent: Mapped[int] = mapped_column(Integer)
    question_count: Mapped[int] = mapped_column(Integer)
    casa_weak_areas: Mapped[list] = mapped_column(JSON, default=list)
    fuel_policy: Mapped[str] = mapped_column(Text, default="")
    units: Mapped[list["ExamUnit"]] = relationship(back_populates="exam", order_by="ExamUnit.position", cascade="all, delete-orphan")


class ExamUnit(Base):
    __tablename__ = "exam_units"
    exam_code: Mapped[str] = mapped_column(ForeignKey("exams.code"), primary_key=True)
    unit_code: Mapped[str] = mapped_column(ForeignKey("units.code"), primary_key=True)
    weight: Mapped[int] = mapped_column(Integer)  # relative share of exam questions
    position: Mapped[int] = mapped_column(Integer)
    exam: Mapped["Exam"] = relationship(back_populates="units")
    unit: Mapped["Unit"] = relationship()


class Unit(Base):
    __tablename__ = "units"
    code: Mapped[str] = mapped_column(String(8), primary_key=True)  # e.g. RBKA
    number: Mapped[str] = mapped_column(String(12))  # e.g. 1.1.2
    title: Mapped[str] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(Integer)  # syllabus order
    topics: Mapped[list["Topic"]] = relationship(back_populates="unit", order_by="Topic.position", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)  # "RBKA 3"
    unit_code: Mapped[str] = mapped_column(ForeignKey("units.code"))
    number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    note: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)
    unit: Mapped["Unit"] = relationship(back_populates="topics")
    subtopics: Mapped[list["Subtopic"]] = relationship(back_populates="topic", order_by="Subtopic.position", cascade="all, delete-orphan")


class Subtopic(Base):
    """The study unit of the app: one note, one progress status, one planner item."""
    __tablename__ = "subtopics"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)  # "RBKA 3.6"
    unit_code: Mapped[str] = mapped_column(ForeignKey("units.code"))
    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"))
    number: Mapped[str] = mapped_column(String(8))  # "3.6"
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(80))  # "3.6-stalling-spinning-and-spiral-dives"
    position: Mapped[int] = mapped_column(Integer)  # global syllabus order across all units
    topic: Mapped["Topic"] = relationship(back_populates="subtopics")
    unit: Mapped["Unit"] = relationship()
    elements: Mapped[list["Element"]] = relationship(back_populates="subtopic", order_by="Element.position", cascade="all, delete-orphan")
    note: Mapped["Note | None"] = relationship(back_populates="subtopic", uselist=False, cascade="all, delete-orphan")
    progress: Mapped["Progress | None"] = relationship(uselist=False)
    equations: Mapped[list["Equation"]] = relationship(secondary="equation_lessons", order_by="Equation.position", viewonly=True)


class Element(Base):
    """A knowledge element from the MOS, e.g. 'RBKA 3.6.2'. Questions and cards tag these."""
    __tablename__ = "elements"
    code: Mapped[str] = mapped_column(String(16), primary_key=True)
    subtopic_id: Mapped[str] = mapped_column(ForeignKey("subtopics.id"))
    number: Mapped[str] = mapped_column(String(12))
    text: Mapped[str] = mapped_column(Text)
    items: Mapped[list] = mapped_column(JSON, default=list)  # [{label, text, subitems:[{label,text}]}]
    position: Mapped[int] = mapped_column(Integer)
    subtopic: Mapped["Subtopic"] = relationship(back_populates="elements")


class Note(Base):
    __tablename__ = "notes"
    subtopic_id: Mapped[str] = mapped_column(ForeignKey("subtopics.id"), primary_key=True)
    path: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200))
    markdown: Mapped[str] = mapped_column(Text)
    html: Mapped[str] = mapped_column(Text)
    references: Mapped[list] = mapped_column(JSON, default=list)
    minutes: Mapped[int | None] = mapped_column(Integer)  # planner reading time: frontmatter override or loader.estimate_minutes()
    subtopic: Mapped["Subtopic"] = relationship(back_populates="note")


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)  # e.g. "RBKA-036"
    unit_code: Mapped[str] = mapped_column(ForeignKey("units.code"))
    subtopic_id: Mapped[str | None] = mapped_column(ForeignKey("subtopics.id"))
    kind: Mapped[str] = mapped_column(String(8))  # mcq | numeric
    stem: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list)  # mcq: 4 strings
    answer: Mapped[str] = mapped_column(String(200))  # mcq: option index "0".."3"; numeric: number
    tolerance: Mapped[float] = mapped_column(Float, default=0.0)  # numeric: +/- accepted
    unit_label: Mapped[str | None] = mapped_column(String(20))  # numeric: "kg", "ft", "min"
    explanation: Mapped[str] = mapped_column(Text)
    references: Mapped[list] = mapped_column(JSON, default=list)
    workbook_page: Mapped[int | None] = mapped_column(Integer)
    difficulty: Mapped[int] = mapped_column(Integer, default=2)  # 1 easy .. 3 hard
    elements: Mapped[list["QuestionElement"]] = relationship(cascade="all, delete-orphan")

    @property
    def element_codes(self) -> list[str]:
        return [qe.element_code for qe in self.elements]


class QuestionElement(Base):
    __tablename__ = "question_elements"
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), primary_key=True)
    element_code: Mapped[str] = mapped_column(ForeignKey("elements.code"), primary_key=True)


class Card(Base):
    __tablename__ = "cards"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    unit_code: Mapped[str] = mapped_column(ForeignKey("units.code"))
    subtopic_id: Mapped[str | None] = mapped_column(ForeignKey("subtopics.id"))
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)
    elements: Mapped[list["CardElement"]] = relationship(cascade="all, delete-orphan")
    review: Mapped["CardReview | None"] = relationship(uselist=False)


class CardElement(Base):
    __tablename__ = "card_elements"
    card_id: Mapped[str] = mapped_column(ForeignKey("cards.id"), primary_key=True)
    element_code: Mapped[str] = mapped_column(ForeignKey("elements.code"), primary_key=True)


class Equation(Base):
    """One formula on the equation sheet (content/equations.yaml); rebuilt from scratch on every seed."""
    __tablename__ = "equations"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)  # slug, e.g. "stall-speed-in-turn"
    name: Mapped[str] = mapped_column(String(200))
    topic: Mapped[str] = mapped_column(String(40))  # a topic id from equations.yaml, e.g. "aerodynamics"
    latex: Mapped[str] = mapped_column(Text)  # KaTeX source without delimiters
    symbols: Mapped[list] = mapped_column(JSON, default=list)  # [{sym, meaning, unit}]
    when: Mapped[str] = mapped_column(Text, default="")
    when_html: Mapped[str] = mapped_column(Text, default="")
    rule_of_thumb: Mapped[str] = mapped_column(Text, default="")
    rule_html: Mapped[str] = mapped_column(Text, default="")
    exams: Mapped[list] = mapped_column(JSON, default=list)  # ["RPLA", "PPLA"]
    tags: Mapped[list] = mapped_column(JSON, default=list)
    see_also: Mapped[list] = mapped_column(JSON, default=list)  # equation ids
    position: Mapped[int] = mapped_column(Integer)  # sheet order
    lessons: Mapped[list["EquationLesson"]] = relationship(order_by="EquationLesson.position", cascade="all, delete-orphan")

    @property
    def lesson_ids(self) -> list[str]:
        return [el.subtopic_id for el in self.lessons]


class EquationLesson(Base):
    __tablename__ = "equation_lessons"
    equation_id: Mapped[str] = mapped_column(ForeignKey("equations.id"), primary_key=True)
    subtopic_id: Mapped[str] = mapped_column(ForeignKey("subtopics.id"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer)  # 0 = the equation's primary lesson


# ---------------------------------------------------------------- user state
STATUSES = ("not_started", "studying", "confident")


class Progress(Base):
    __tablename__ = "progress"
    subtopic_id: Mapped[str] = mapped_column(ForeignKey("subtopics.id"), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), default="not_started")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


# Student annotations on lessons: typed notes, text highlights and Pencil ink (see services.annotations).
HIGHLIGHT_COLOURS = ("yellow", "green", "pink", "blue")
INK_KINDS = ("lesson", "sketch")  # lesson: overlay on the lesson text (page 0); sketch: sketch-pad pages


class StudentNote(Base):
    """The student's own typed notes for one lesson (named to stay clear of the content Note)."""
    __tablename__ = "student_notes"
    subtopic_id: Mapped[str] = mapped_column(ForeignKey("subtopics.id"), primary_key=True)
    text: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Highlight(Base):
    """A highlighted passage, anchored by its text (W3C TextQuoteSelector) with a position fast path."""
    __tablename__ = "highlights"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subtopic_id: Mapped[str] = mapped_column(ForeignKey("subtopics.id"), index=True)
    colour: Mapped[str] = mapped_column(String(8), default="yellow")  # one of HIGHLIGHT_COLOURS
    exact: Mapped[str] = mapped_column(Text)
    prefix: Mapped[str] = mapped_column(String(64), default="")
    suffix: Mapped[str] = mapped_column(String(64), default="")
    start: Mapped[int] = mapped_column(Integer)  # character offsets in the lesson's text map
    end: Mapped[int] = mapped_column(Integer)
    block_id: Mapped[str | None] = mapped_column(String(80))  # nearest heading/block id, a hint only
    comment: Mapped[str] = mapped_column(Text, default="")
    orphaned: Mapped[bool] = mapped_column(Boolean, default=False)  # text no longer found in the lesson
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class InkDocument(Base):
    """Pencil strokes for one lesson overlay or one sketch-pad page; `rev` increments on every save."""
    __tablename__ = "ink_documents"
    __table_args__ = (UniqueConstraint("subtopic_id", "kind", "page"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subtopic_id: Mapped[str] = mapped_column(ForeignKey("subtopics.id"), index=True)
    kind: Mapped[str] = mapped_column(String(8))  # one of INK_KINDS
    page: Mapped[int] = mapped_column(Integer, default=0)
    strokes: Mapped[list] = mapped_column(JSON, default=list)
    rev: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Attempt(Base):
    """A practice quiz or a timed mock exam."""
    __tablename__ = "attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mode: Mapped[str] = mapped_column(String(8))  # quiz | exam
    exam_code: Mapped[str | None] = mapped_column(ForeignKey("exams.code"))
    title: Mapped[str] = mapped_column(String(200), default="")
    config: Mapped[dict] = mapped_column(JSON, default=dict)  # units/subtopics requested etc.
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    deadline: Mapped[datetime | None] = mapped_column(DateTime)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    score_percent: Mapped[float | None] = mapped_column(Float)
    passed: Mapped[bool | None] = mapped_column(Boolean)
    answers: Mapped[list["AttemptAnswer"]] = relationship(back_populates="attempt", order_by="AttemptAnswer.position", cascade="all, delete-orphan")


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id"))
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    position: Mapped[int] = mapped_column(Integer)
    given: Mapped[str | None] = mapped_column(String(200))
    correct: Mapped[bool | None] = mapped_column(Boolean)
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime)
    attempt: Mapped["Attempt"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship()


class CardReview(Base):
    """SM-2 state for one card."""
    __tablename__ = "card_reviews"
    card_id: Mapped[str] = mapped_column(ForeignKey("cards.id"), primary_key=True)
    ease: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    due: Mapped[date] = mapped_column(Date, default=date.today)
    last_grade: Mapped[int | None] = mapped_column(Integer)
    last_reviewed: Mapped[datetime | None] = mapped_column(DateTime)
    lapses: Mapped[int] = mapped_column(Integer, default=0)



class StudyPlan(Base):
    __tablename__ = "study_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_date: Mapped[date] = mapped_column(Date)
    rpla_exam_date: Mapped[date] = mapped_column(Date)
    ppla_exam_date: Mapped[date] = mapped_column(Date)
    study_weekdays: Mapped[list] = mapped_column(JSON, default=lambda: [0, 1, 2, 3, 4, 5])  # Mon=0 .. Sun=6
    minutes_per_session: Mapped[int] = mapped_column(Integer, default=60)
    revision_days_before_exam: Mapped[int] = mapped_column(Integer, default=4)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    shortfall: Mapped[dict | None] = mapped_column(JSON)  # set when the content does not fit; see services.planner
    items: Mapped[list["PlanItem"]] = relationship(back_populates="plan", order_by="(PlanItem.date, PlanItem.position)", cascade="all, delete-orphan")


PLAN_ITEM_KINDS = ("study", "quiz", "cards", "mock_exam", "revision")


class PlanItem(Base):
    __tablename__ = "plan_items"
    __table_args__ = (UniqueConstraint("plan_id", "date", "position"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("study_plans.id"))
    date: Mapped[date] = mapped_column(Date)
    position: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(12))
    subtopic_id: Mapped[str | None] = mapped_column(ForeignKey("subtopics.id"))
    exam_code: Mapped[str | None] = mapped_column(ForeignKey("exams.code"))  # which exam block this belongs to
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=0)
    label: Mapped[str] = mapped_column(String(200), default="")
    done_at: Mapped[datetime | None] = mapped_column(DateTime)
    plan: Mapped["StudyPlan"] = relationship(back_populates="items")
    subtopic: Mapped["Subtopic | None"] = relationship()
