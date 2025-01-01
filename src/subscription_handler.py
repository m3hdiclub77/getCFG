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
            # Remove whitespace and newlines
            s = s.strip()
            # Check if string contains only valid base64 characters
            if not re.match('^[A-Za-z0-9+/]*={0,2}$', s):
                return False
            # Try to decode
            decoded = base64.b64decode(s)
            # Try to decode as UTF-8 to make sure it's valid text
            decoded.decode('utf-8')
            return True
        except:
            return False

    def decode_base64_content(self, content: str) -> str:
        """Decode base64 content."""
        try:
            # Remove any whitespace and newlines
            content = content.strip()
            # Decode base64
            decoded = base64.b64decode(content)
            # Convert to string
            return decoded.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error decoding base64 content: {str(e)}")
            return content

    def extract_configs(self, content: str) -> List[str]:
        """Extract configs from decoded content."""
        configs = []
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with any supported protocol
            if any(line.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                configs.append(line)
                
        return configs

    def parse_subscription_content(self, content: str) -> List[str]:
        """Parse subscription content and extract proxy configurations."""
        if not content:
            return []

        # First try to decode the entire content if it's base64
        decoded_content = content
        if self.is_base64(content):
            self.logger.info("Content is base64 encoded, decoding...")
            decoded_content = self.decode_base64_content(content)
            
        # Extract configs from decoded content
        configs = self.extract_configs(decoded_content)
        
        # Remove duplicates while preserving order
        unique_configs = list(dict.fromkeys(configs))
        
        self.logger.info(f"Found {len(unique_configs)} unique configs")
        return unique_configs

    def process_subscription_url(self, url: str) -> List[str]:
        """Process a subscription URL and return list of valid configs."""
        content = self.fetch_subscription(url)
        if content:
            return self.parse_subscription_content(content)
        return []
