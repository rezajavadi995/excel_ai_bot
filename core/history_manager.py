# core/history_manager.py

import os
import shutil
from datetime import datetime

class HistoryManager:
    def __init__(self, base_dir="storage/versions"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save_version(self, file_id, source_file, tag):
        file_dir = os.path.join(self.base_dir, file_id)
        os.makedirs(file_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_name = f"{timestamp}_{tag}.xlsx"
        dest_path = os.path.join(file_dir, version_name)

        shutil.copy2(source_file, dest_path)
        return dest_path

    def list_versions(self, file_id):
        file_dir = os.path.join(self.base_dir, file_id)
        if not os.path.exists(file_dir):
            return []
        return sorted(os.listdir(file_dir))
