import requests
import base64
from typing import List, Optional
from urllib.parse import urlparse
import logging

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

    def decode_base64_recursively(encoded: str) -> str:
    """Decode Base64 content recursively until it's no longer decodable."""
    try:
        while True:
            decoded = base64.b64decode(encoded).decode('utf-8')
            if decoded == encoded:  # If no change occurs, stop decoding
                break
            encoded = decoded
        return encoded
    except Exception:
        return encoded

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
                    decoded = decode_base64_recursively(line)
                    if any(decoded.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                        line = decoded
            except Exception as e:
                self.logger.warning(f"Failed to decode line: {line}, error: {e}")

            if any(line.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                configs.append(line)

        return configs

    def process_subscription_url(self, url: str) -> List[str]:
        """Process a subscription URL and return list of valid configs."""
        content = self.fetch_subscription(url)
        if content:
            return self.parse_subscription_content(content)
        return []
