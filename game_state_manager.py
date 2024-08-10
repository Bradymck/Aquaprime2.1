import os
import json
import git
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import logging
import shutil
from datetime import datetime

# Setup logging
logger = logging.getLogger('GameStateManager')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///game_state.db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

class GameStateManager:
    def __init__(self, repo_path, file_path):
        self.repo_path = repo_path
        self.file_path = file_path
        self.repo = git.Repo(repo_path)
        self.game_state = self.load_game_state()

    def load_game_state(self):
        if os.path.exists(self.file_path):
            with open(self.file_path) as f:
                return json.load(f)
        return {}

    def save_game_state(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.game_state, f, indent=4)

    def update_state(self, new_memory):
        self.game_state['memory'] = self.game_state.get('memory', []) + [new_memory]
        self.save_game_state()

    # Additional methods if needed