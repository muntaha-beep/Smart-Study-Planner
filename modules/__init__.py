"""
modules/__init__.py

The backend (business logic) layer. The GUI talks to these classes and never
touches the database directly:

    subject_manager.py   - SubjectManager   (subjects)
    topic_manager.py     - TopicManager     (topics, filters, sorting)
    study_planner.py     - StudyPlanner     (smart plan generator)
    schedule_manager.py  - ScheduleManager  (saved study sessions)
    progress_tracker.py  - ProgressTracker  (progress and dashboard numbers)
"""