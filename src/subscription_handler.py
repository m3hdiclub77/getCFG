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
            self.logger.info(f"Fetching content from {url}")
            response = requests.get(url, headers=self.config.HEADERS, 
                                 timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            content = response.text
            self.logger.info(f"Received content length: {len(content)} characters")
            # Log first 100 characters of content for debugging
            self.logger.debug(f"Content preview: {content[:100]}...")
            return content
        except Exception as e:
            self.logger.error(f"Error fetching subscription from {url}: {str(e)}")
            return None

    def is_base64(self, s: str) -> bool:
        """Check if a string is base64 encoded."""
        try:
            # Remove whitespace and newlines
            s = s.strip()
            # Add padding if necessary
            missing_padding = len(s) % 4
            if missing_padding:
                s += '=' * (4 - missing_padding)
            
            # Check if string contains only valid base64 characters
            if not re.match('^[A-Za-z0-9+/]*={0,2}$', s):
                return False
                
            # Try to decode
            decoded = base64.b64decode(s)
            # Try to decode as UTF-8 to make sure it's valid text
            decoded.decode('utf-8')
            return True
        except Exception as e:
            self.logger.debug(f"Base64 check failed: {str(e)}")
            return False

    def decode_base64_content(self, content: str) -> str:
        """Decode base64 content."""
        try:
            # Remove any whitespace and newlines
            content = content.strip()
            # Add padding if necessary
            missing_padding = len(content) % 4
            if missing_padding:
                content += '=' * (4 - missing_padding)
                
            # Decode base64
            decoded = base64.b64decode(content)
            # Convert to string
            result = decoded.decode('utf-8')
            self.logger.info(f"Successfully decoded base64 content, length: {len(result)}")
            self.logger.debug(f"Decoded content preview: {result[:100]}...")
            return result
        except Exception as e:
            self.logger.error(f"Error decoding base64 content: {str(e)}")
            return content

    def extract_configs(self, content: str) -> List[str]:
        """Extract configs from decoded content."""
        configs = []
        lines = content.split('\n')
        self.logger.info(f"Processing {len(lines)} lines for config extraction")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with any supported protocol
            for protocol in self.config.SUPPORTED_PROTOCOLS:
                if line.startswith(protocol):
                    self.logger.debug(f"Found {protocol} config: {line[:50]}...")
                    configs.append(line)
                    break
                
        self.logger.info(f"Extracted {len(configs)} configs")
        return configs

    def parse_subscription_content(self, content: str) -> List[str]:
        """Parse subscription content and extract proxy configurations."""
        if not content:
            self.logger.warning("Received empty content")
            return []

        # First try to decode the entire content if it's base64
        decoded_content = content
        if self.is_base64(content):
            self.logger.info("Content is base64 encoded, decoding...")
            decoded_content = self.decode_base64_content(content)
        else:
            self.logger.info("Content is not base64 encoded")
            
        # Extract configs from decoded content
        configs = self.extract_configs(decoded_content)
        
        # Remove duplicates while preserving order
        unique_configs = list(dict.fromkeys(configs))
        
        self.logger.info(f"Found {len(unique_configs)} unique configs")
        return unique_configs

    def process_subscription_url(self, url: str) -> List[str]:
        """Process a subscription URL and return list of valid configs."""
        self.logger.info(f"Processing subscription URL: {url}")
        content = self.fetch_subscription(url)
        if content:
            configs = self.parse_subscription_content(content)
            self.logger.info(f"Successfully processed {url}, found {len(configs)} configs")
            return configs
        return []
