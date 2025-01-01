import requests
import base64
from typing import List, Optional
import logging
import re
import json
from datetime import datetime
import os

class SubscriptionHandler:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Create configs directory if it doesn't exist
        os.makedirs('configs', exist_ok=True)
        
    def fetch_subscription(self, url: str) -> Optional[str]:
        """Fetch content from subscription URL."""
        try:
            self.logger.info(f"Fetching content from {url}")
            response = requests.get(url, headers=self.config.HEADERS, 
                                 timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            content = response.text
            self.logger.info(f"Received content length: {len(content)} characters")
            return content
        except Exception as e:
            self.logger.error(f"Error fetching subscription from {url}: {str(e)}")
            return None

    def is_base64(self, s: str) -> bool:
        """Check if a string is base64 encoded with more flexible validation."""
        if not s:
            return False
            
        try:
            # Remove whitespace and newlines
            s = s.strip()
            # Add padding if necessary
            missing_padding = len(s) % 4
            if missing_padding:
                s += '=' * (4 - missing_padding)
            
            # Less restrictive pattern that allows for URL-safe base64
            if not re.match('^[A-Za-z0-9+/\-_]*={0,3}$', s):
                return False
                
            # Try to decode
            base64.b64decode(s, validate=True)
            return True
        except Exception as e:
            self.logger.debug(f"Base64 check failed: {str(e)}")
            return False

    def decode_base64_content(self, content: str) -> str:
        """Decode base64 content with support for URL-safe encoding."""
        try:
            # Remove any whitespace and newlines
            content = content.strip()
            # Add padding if necessary
            missing_padding = len(content) % 4
            if missing_padding:
                content += '=' * (4 - missing_padding)
            
            # Try standard base64 first
            try:
                decoded = base64.b64decode(content)
            except:
                # If standard fails, try URL-safe base64
                decoded = base64.urlsafe_b64decode(content)
                
            # Convert to string
            result = decoded.decode('utf-8')
            self.logger.info(f"Successfully decoded base64 content, length: {len(result)}")
            return result
        except Exception as e:
            self.logger.error(f"Error decoding base64 content: {str(e)}")
            return content

    def extract_configs(self, content: str) -> List[str]:
        """Extract configs from decoded content with improved protocol detection."""
        configs = []
        # Split by both newlines and commas (some subscriptions use comma separation)
        for line in re.split(r'[\n,]', content):
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with any supported protocol
            if any(line.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                configs.append(line)
                self.logger.debug(f"Found config: {line[:50]}...")
        
        self.logger.info(f"Extracted {len(configs)} configs")
        return configs

    def parse_subscription_content(self, content: str) -> List[str]:
        """Parse subscription content with improved base64 handling."""
        if not content:
            self.logger.warning("Received empty content")
            return []

        # Check if content might be base64 encoded
        if self.is_base64(content):
            self.logger.info("Content appears to be base64 encoded, attempting decode...")
            decoded_content = self.decode_base64_content(content)
            if decoded_content != content:  # Check if decoding actually changed something
                self.logger.info("Successfully decoded base64 content")
                return self.extract_configs(decoded_content)
        
        # If not base64 or decoding failed, try direct extraction
        self.logger.info("Processing content as plain text")
        return self.extract_configs(content)

    def process_subscription_url(self, url: str) -> List[str]:
        """Process a subscription URL and return list of valid configs."""
        self.logger.info(f"Processing subscription URL: {url}")
        content = self.fetch_subscription(url)
        if content:
            configs = self.parse_subscription_content(content)
            self.logger.info(f"Successfully processed {url}, found {len(configs)} configs")
            return configs
        return []

    def save_configs(self, configs: List[str]) -> bool:
        """Save configs to output file."""
        try:
            # Convert configs to base64
            combined = '\n'.join(configs)
            encoded = base64.b64encode(combined.encode()).decode()
            
            # Save to file
            with open(self.config.OUTPUT_FILE, 'w') as f:
                f.write(encoded)
            
            self.logger.info(f"Successfully saved {len(configs)} configs to {self.config.OUTPUT_FILE}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configs: {str(e)}")
            return False

    def save_stats(self, protocol_stats: Dict[str, int]):
        """Save channel statistics."""
        try:
            stats = {
                'last_update': datetime.now().isoformat(),
                'protocol_stats': protocol_stats
            }
            
            with open(self.config.STATS_FILE, 'w') as f:
                json.dump(stats, f, indent=2)
                
            self.logger.info(f"Channel statistics saved to {self.config.STATS_FILE}")
        except Exception as e:
            self.logger.error(f"Error saving channel statistics: {str(e)}")
