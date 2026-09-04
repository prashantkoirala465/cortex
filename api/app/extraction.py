from rq.exceptions import NoSuchJobError
from rq.job import Job
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExtractionJob, JobStatus, Note
from app.queue import extraction_queue, redis_conn
from app.tasks import process_note


def enqueue_extraction(db: Session, note: Note) -> ExtractionJob:
    """Queues extraction for a note, superseding any run for the same note
    that hasn't started yet - so a burst of autosaves collapses into one
    processing run of the latest content instead of queuing every edit."""
    pending = db.scalar(
        select(ExtractionJob)
        .where(ExtractionJob.note_id == note.id, ExtractionJob.status == JobStatus.pending.value)
        .order_by(ExtractionJob.created_at.desc())
    )
    if pending is not None:
        if pending.rq_job_id:
            try:
                Job.fetch(pending.rq_job_id, connection=redis_conn).cancel()
            except NoSuchJobError:
                pass
        pending.status = JobStatus.cancelled.value
        db.commit()

    job = ExtractionJob(note_id=note.id, status=JobStatus.pending.value)
    db.add(job)
    db.commit()
    db.refresh(job)

    rq_job = extraction_queue.enqueue(process_note, str(note.id), str(job.id))
    job.rq_job_id = rq_job.id
    db.commit()
    return job
