import requests
import base64
from typing import List, Optional
from urllib.parse import urlparse
import logging
import re

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

    def is_base64(self, s: str) -> bool:
        """Check if a string is base64 encoded."""
        try:
            # Check if string contains only valid base64 characters
            if not re.match('^[A-Za-z0-9+/]*={0,2}$', s):
                return False
            # Try to decode
            base64.b64decode(s)
            return True
        except:
            return False

    def decode_base64_content(self, content: str) -> str:
        """Decode base64 content if encoded."""
        try:
            # Try to decode base64
            decoded = base64.b64decode(content).decode('utf-8')
            return decoded
        except:
            return content

    def parse_subscription_content(self, content: str) -> List[str]:
        """Parse subscription content and extract proxy configurations."""
        configs = []
        if not content:
            return configs

        # First try to decode the entire content if it's base64
        if self.is_base64(content):
            content = self.decode_base64_content(content)

        # Split into lines and process each line
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to decode each line if it's base64
            if self.is_base64(line):
                decoded_line = self.decode_base64_content(line)
                # Check if decoded content is a valid config
                if any(decoded_line.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                    configs.append(decoded_line)
            elif any(line.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                configs.append(line)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(configs))

    def process_subscription_url(self, url: str) -> List[str]:
        """Process a subscription URL and return list of valid configs."""
        content = self.fetch_subscription(url)
        if content:
            configs = self.parse_subscription_content(content)
            self.logger.info(f"Found {len(configs)} configs in subscription {url}")
            return configs
        return []
