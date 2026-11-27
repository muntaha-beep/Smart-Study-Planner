"""
ui/__init__.py

The graphical (Tkinter) layer. Pages only talk to the backend classes in
modules/ and never write SQL:

    styles.py          - colours, fonts and small reusable widgets
    dashboard.py       - home screen with statistic cards
    subjects_page.py   - subject management
    topics_page.py     - study topic management
    planner_page.py    - smart study plan generator
    schedule_page.py   - saved study sessions
    progress_page.py   - progress tracking
    algorithm_page.py  - algorithm demonstration and analysis
"""