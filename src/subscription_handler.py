import requests
import base64
import os
import shutil
import logging
from typing import List, Optional
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


class SubscriptionHandler:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def fetch_subscription(self, url: str) -> Optional[str]:
        """Fetch content from subscription URL."""
        try:
            response = requests.get(url, headers=self.config.HEADERS, 
                                 timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Error fetching subscription from {url}: {str(e)}")
            return None

    def parse_subscription_content(self, content: str) -> List[str]:
        """Parse subscription content and extract proxy configurations."""
        configs = []
        if not content:
            return configs

        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            try:
                if not any(line.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                    decoded = base64.b64decode(line).decode('utf-8')
                    if any(decoded.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                        line = decoded
            except:
                pass

            if any(line.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                configs.append(line)

        return configs

    def process_subscription_url(self, url: str) -> List[str]:
        """Process a subscription URL and return list of valid configs."""
        content = self.fetch_subscription(url)
        if content:
            return self.parse_subscription_content(content)
        return []
        
    def secure_file_write(path: Path, content: str):
    # Ensure directory exists and is secure
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    
    # Write with secure permissions
    temp_path = path.with_suffix('.tmp')
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(content)
    os.chmod(temp_path, 0o644)
    temp_path.replace(path)
    
    def create_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.config.BASE_DIR / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / f"subscription_backup_{timestamp}"
        shutil.copy2(self.config.OUTPUT_FILE, backup_path)
        
        # Cleanup old backups
        backup_files = sorted(backup_dir.glob("subscription_backup_*"))
        while len(backup_files) > 5:  # Keep last 5 backups
            backup_files[0].unlink()
            backup_files = backup_files[1:]

    def fetch_all_subscriptions(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.process_subscription_url, url) 
                      for url in self.config.SUBSCRIPTION_URLS]
            return [f.result() for f in futures]
